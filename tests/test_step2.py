import copy
import os
from types import SimpleNamespace

import pytest

from mini_calude_code import step1, step2


class FakeCompletions:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def create(self, **kwargs):
        # Copy so later appends to the list don't change what we recorded.
        self.calls.append(copy.deepcopy(kwargs))
        message = SimpleNamespace(content=next(self.replies))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def fake_client(*replies):
    completions = FakeCompletions(replies)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


def test_chat_returns_reply_and_records_both_turns():
    client, _ = fake_client("Hi Shivin!")
    messages = []

    reply = step2.chat(client, messages, "My name is Shivin")

    assert reply == "Hi Shivin!"
    assert messages == [
        {"role": "user", "content": "My name is Shivin"},
        {"role": "assistant", "content": "Hi Shivin!"},
    ]


def test_chat_sends_full_history_each_turn():
    client, completions = fake_client("Hi Shivin!", "Your name is Shivin.")
    messages = []

    step2.chat(client, messages, "My name is Shivin")
    step2.chat(client, messages, "What is my name?")

    first, second = completions.calls
    assert first["model"] == step1.MODEL
    assert first["messages"] == [{"role": "user", "content": "My name is Shivin"}]
    assert second["messages"] == [
        {"role": "user", "content": "My name is Shivin"},
        {"role": "assistant", "content": "Hi Shivin!"},
        {"role": "user", "content": "What is my name?"},
    ]


@pytest.mark.skipif(not os.environ.get("RUN_LIVE_TESTS"), reason="set RUN_LIVE_TESTS=1 to call the real Groq API")
def test_chat_live_remembers_context():
    client = step1.make_client()
    messages = []

    step2.chat(client, messages, "My favourite colour is teal. Just say OK.")
    reply = step2.chat(client, messages, "What is my favourite colour? Answer in one word.")

    assert "teal" in reply.lower()
