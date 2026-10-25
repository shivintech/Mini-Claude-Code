import os
from types import SimpleNamespace

import pytest

from mini_calude_code import step1


class FakeCompletions:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def fake_client(reply="An agent acts on its own."):
    completions = FakeCompletions(reply)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


def test_ask_returns_reply_text():
    client, _ = fake_client("An agent acts on its own.")

    assert step1.ask(client, "What is an agent?") == "An agent acts on its own."


def test_ask_sends_prompt_as_user_message():
    client, completions = fake_client()

    step1.ask(client, "What is an agent?")

    assert len(completions.calls) == 1
    call = completions.calls[0]
    assert call["model"] == step1.MODEL
    assert call["messages"] == [{"role": "user", "content": "What is an agent?"}]


def test_make_client_uses_groq(monkeypatch):
    monkeypatch.setattr(step1, "load_dotenv", lambda: None)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")

    client = step1.make_client()

    assert client.api_key == "gsk_test"
    assert str(client.base_url).startswith("https://api.groq.com/openai/v1")


def test_make_client_requires_key(monkeypatch):
    monkeypatch.setattr(step1, "load_dotenv", lambda: None)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(KeyError):
        step1.make_client()


@pytest.mark.skipif(not os.environ.get("RUN_LIVE_TESTS"), reason="set RUN_LIVE_TESTS=1 to call the real Groq API")
def test_ask_live():
    reply = step1.ask(step1.make_client(), "Reply with just the word: pong")

    assert "pong" in reply.lower()
