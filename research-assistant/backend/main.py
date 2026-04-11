from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={
    r"/chat": {
        "origins": ["https://research-assistant-app-636745240622.us-central1.run.app"]
    }
})

# Set this in Cloud Run env vars
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

LLM_URL = "https://openrouter.ai/api/v1/chat/completions"

# -----------------------------
# Health Check
# -----------------------------
@app.route("/")
def health():
    return "OK"


# -----------------------------
# Chat Endpoint
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    user_message = data.get("message", "")
    history = data.get("history", [])

    try:
        # -----------------------------
        # System Prompt
        # -----------------------------
        system_prompt = """
            You are an AI assistant being developed for an Animal Rescue Research platform.

            If the user asks about:
                - animal rescue
                - stray animals
                - trends
                - shelters
                - analysis
                - data insights

            Respond with:
                "I'm currently being built. Soon I will be able to analyze animal rescue data, generate charts, and provide insights such as trends, comparisons, and statistics."

            For general questions (jokes, facts, etc), respond normally.
        """

        # -----------------------------
        # Build Messages
        # -----------------------------
        messages = [{"role": "system", "content": system_prompt}]

        # Add history if provided
        for msg in history:
            messages.append(msg)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # -----------------------------
        # Call LLM
        # -----------------------------
        response = requests.post(
            LLM_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mixtral-8x7b-instruct",  # free model
                "messages": messages,
                "temperature": 0.7
            }
        )

        result = response.json()

        assistant_reply = result["choices"][0]["message"]["content"]

        return jsonify({
            "response": assistant_reply
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
