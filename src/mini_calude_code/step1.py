import os

from dotenv import load_dotenv
from openai import OpenAI

MODEL = "openai/gpt-oss-120b"


def make_client() -> OpenAI:
    load_dotenv()  # loads GROQ_API_KEY from the project's .env file
    return OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )


def ask(client: OpenAI, prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print(ask(make_client(), "Explain what an AI agent is in one sentence."))
