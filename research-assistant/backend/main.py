import os
import uuid
import traceback

import pandas as pd
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from agent import run_agent_loop, stream_agent_loop, sse
from tools import clean_dataframe

app = Flask(__name__)
CORS(app)


@app.route("/")
def health():
    return "OK"


@app.route("/stream", methods=["POST"])
def stream_chat():
    data = request.get_json()
    user_message = data.get("message", "")
    history = data.get("history", [])
    csv_context = data.get("csv_context")

    def generate():
        try:
            yield from stream_agent_loop(user_message, history, csv_context=csv_context)
        except Exception as e:
            traceback.print_exc()
            yield sse({"type": "error", "content": str(e)})
            yield sse({"type": "done"})

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    history = data.get("history", [])
    csv_context = data.get("csv_context")

    try:
        result = run_agent_loop(user_message, history, csv_context=csv_context)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename.endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400

    try:
        df = pd.read_csv(f)
        df = clean_dataframe(df)
        rows, cols = df.shape
        preview = df.head(5).values.tolist()
        columns = list(df.columns)

        upload_dir = "/tmp/csv_uploads"
        os.makedirs(upload_dir, exist_ok=True)
        csv_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}.csv")
        df.to_csv(csv_path, index=False)

        return jsonify(
            {
                "rows": rows,
                "columns": columns,
                "preview": preview,
                "csv_path": csv_path,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
