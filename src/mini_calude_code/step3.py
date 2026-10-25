import json

from openai import OpenAI

from mini_calude_code.step1 import MODEL, make_client


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File {path} not found"


TOOLS = {"read_file": read_file}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path of the file to read"},
                },
                "required": ["path"],
            },
        },
    },
]


def run_tool(name: str, arguments: str) -> str:
    if name not in TOOLS:
        return f"Unknown tool: {name}"
    args = json.loads(arguments)
    print(f"Model wants to run: {name}({args})")
    return TOOLS[name](**args)


def run_agent(client: OpenAI, messages: list[dict]) -> str:
    """Call the model in a loop, running any tools it asks for, until it gives a normal answer."""
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        message = response.choices[0].message

        # No tool calls means the model is done and gave us a normal answer
        if not message.tool_calls:
            messages.append({"role": "assistant", "content": message.content})
            return message.content

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in message.tool_calls
            ],
        })

        for tool_call in message.tool_calls:
            result = run_tool(tool_call.function.name, tool_call.function.arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })


if __name__ == "__main__":
    messages = [
        {"role": "user", "content": "What is inside notes.txt, notes1.txt and notes2.txt? Summarize it in one line."},
    ]
    print(run_agent(make_client(), messages))
