import os
import json
import anthropic

from config import SYSTEM_PROMPT, TOOLS, TOOL_LABELS
from tools import execute_tool, build_csv_context

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-opus-4-7"
MAX_TOOL_ITERATIONS = 8


def sse(obj):
    return f"data: {json.dumps(obj)}\n\n"


def run_agent_loop(user_message, history, csv_context=None):
    messages = []
    for m in history:
        role = m.get("role")
        content = m.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    suffix, csv_code_context = build_csv_context(csv_context)
    messages.append({"role": "user", "content": user_message + suffix})

    all_plots = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            text = "".join(b.text for b in response.content if hasattr(b, "text"))
            return {"type": "result", "response": text, "plots": all_plots}

        if response.stop_reason == "tool_use":
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        }
                    )
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                output, is_error, csv_code_context = execute_tool(
                    block.name, block.input, csv_code_context, all_plots
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                        "is_error": is_error,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

    return {
        "type": "result",
        "response": "I reached the maximum number of analysis steps. Here is what I found.",
        "plots": all_plots,
    }


def stream_agent_loop(user_message, history, csv_context=None):
    messages = []
    for m in history:
        role = m.get("role")
        content = m.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    suffix, csv_code_context = build_csv_context(csv_context)
    messages.append({"role": "user", "content": user_message + suffix})

    all_plots = []

    for _ in range(MAX_TOOL_ITERATIONS):
        blocks = []
        current_idx = None

        with client.messages.stream(
            model=MODEL,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        ) as s:
            for event in s:
                if event.type == "content_block_start":
                    cb = event.content_block
                    if cb.type == "text":
                        blocks.append({"type": "text", "text": ""})
                    elif cb.type == "tool_use":
                        blocks.append(
                            {
                                "type": "tool_use",
                                "id": cb.id,
                                "name": cb.name,
                                "input_str": "",
                                "input": {},
                            }
                        )
                    current_idx = len(blocks) - 1

                elif event.type == "content_block_delta":
                    if current_idx is None:
                        continue
                    b = blocks[current_idx]
                    if event.delta.type == "text_delta":
                        b["text"] += event.delta.text
                        yield sse({"type": "text", "content": event.delta.text})
                    elif event.delta.type == "input_json_delta":
                        b["input_str"] += event.delta.partial_json

                elif event.type == "content_block_stop":
                    if (
                        current_idx is not None
                        and blocks[current_idx]["type"] == "tool_use"
                    ):
                        b = blocks[current_idx]
                        try:
                            b["input"] = (
                                json.loads(b["input_str"]) if b["input_str"] else {}
                            )
                        except Exception:
                            b["input"] = {}
                        label_fn = TOOL_LABELS.get(
                            b["name"], lambda _: f"Using {b['name']}…"
                        )
                        start_evt = {
                            "type": "tool_start",
                            "label": label_fn(b["input"]),
                            "toolName": b["name"],
                        }
                        if b["name"] == "execute_python":
                            start_evt["code"] = b["input"].get("code", "")
                        yield sse(start_evt)

            final_msg = s.get_final_message()
            stop_reason = final_msg.stop_reason

        if stop_reason == "end_turn":
            for plot in all_plots:
                yield sse({"type": "plot", "data": plot})
            yield sse({"type": "done"})
            return

        if stop_reason == "tool_use":
            assistant_content = []
            for b in blocks:
                if b["type"] == "text":
                    assistant_content.append({"type": "text", "text": b["text"]})
                elif b["type"] == "tool_use":
                    assistant_content.append(
                        {
                            "type": "tool_use",
                            "id": b["id"],
                            "name": b["name"],
                            "input": b["input"],
                        }
                    )
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for b in blocks:
                if b["type"] != "tool_use":
                    continue
                output, is_error, csv_code_context = execute_tool(
                    b["name"], b["input"], csv_code_context, all_plots
                )
                yield sse({"type": "tool_done"})
                if b["name"] == "analyze_dataset" and not is_error:
                    try:
                        rd = json.loads(output)
                        yield sse(
                            {
                                "type": "dataset_sample",
                                "dataset": rd.get("dataset", ""),
                                "columns": rd.get("columns", []),
                                "sample": rd.get("sample", []),
                            }
                        )
                    except Exception:
                        pass
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": b["id"],
                        "content": output,
                        "is_error": is_error,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

    for plot in all_plots:
        yield sse({"type": "plot", "data": plot})
    yield sse({"type": "done"})
