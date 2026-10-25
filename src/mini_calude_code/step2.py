from openai import OpenAI

from mini_calude_code.step1 import MODEL, make_client


def chat(client: OpenAI, messages: list[dict], user_input: str) -> str:
    """Send user_input along with the whole conversation so far, and remember the reply."""
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    return reply


if __name__ == "__main__":
    client = make_client()
    messages = []

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ("exit", "quit"):
            break

        print("Bot:", chat(client, messages, user_input))
