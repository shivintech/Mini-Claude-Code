import copy
import json
import os
from types import SimpleNamespace

import pytest

from mini_calude_code import step1, step3


def tool_call(call_id, name, args):
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=json.dumps(args)))


def reply(content=None, tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeCompletions:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def create(self, **kwargs):
        # Copy so later appends to the list don't change what we recorded.
        self.calls.append(copy.deepcopy(kwargs))
        return next(self.responses)


def fake_client(*responses):
    completions = FakeCompletions(responses)
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


def test_read_file_returns_contents(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("buy milk", encoding="utf-8")

    assert step3.read_file(str(path)) == "buy milk"


def test_read_file_missing(tmp_path):
    path = tmp_path / "missing.txt"

    assert step3.read_file(str(path)) == f"File {path} not found"


def test_run_tool_unknown_name():
    assert step3.run_tool("delete_everything", "{}") == "Unknown tool: delete_everything"


def test_run_agent_answers_without_tools():
    client, completions = fake_client(reply("Hello!"))
    messages = [{"role": "user", "content": "Hi"}]

    assert step3.run_agent(client, messages) == "Hello!"
    assert len(completions.calls) == 1
    assert completions.calls[0]["tools"] == step3.TOOL_SCHEMAS


def test_run_agent_runs_tool_and_sends_result_back(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("buy milk", encoding="utf-8")
    client, completions = fake_client(
        reply(tool_calls=[tool_call("call_1", "read_file", {"path": str(path)})]),
        reply("The note says to buy milk."),
    )
    messages = [{"role": "user", "content": "What is in notes.txt?"}]

    answer = step3.run_agent(client, messages)

    assert answer == "The note says to buy milk."
    assert len(completions.calls) == 2
    second_request = completions.calls[1]["messages"]
    assert second_request[1]["tool_calls"][0]["function"]["name"] == "read_file"
    assert second_request[2] == {"role": "tool", "tool_call_id": "call_1", "content": "buy milk"}


def test_run_agent_handles_several_tool_calls_in_one_turn(tmp_path):
    (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
    client, completions = fake_client(
        reply(tool_calls=[
            tool_call("call_1", "read_file", {"path": str(tmp_path / "a.txt")}),
            tool_call("call_2", "read_file", {"path": str(tmp_path / "b.txt")}),
        ]),
        reply("a has alpha, b is missing."),
    )
    messages = [{"role": "user", "content": "Read a.txt and b.txt"}]

    step3.run_agent(client, messages)

    tool_results = [m for m in completions.calls[1]["messages"] if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tool_results] == ["call_1", "call_2"]
    assert tool_results[0]["content"] == "alpha"
    assert "not found" in tool_results[1]["content"]


@pytest.mark.skipif(not os.environ.get("RUN_LIVE_TESTS"), reason="set RUN_LIVE_TESTS=1 to call the real Groq API")
def test_run_agent_live_reads_file(tmp_path):
    path = tmp_path / "secret.txt"
    path.write_text("The password is mango.", encoding="utf-8")
    messages = [{"role": "user", "content": f"Read {path} and tell me the password in one word."}]

    answer = step3.run_agent(step1.make_client(), messages)

    assert "mango" in answer.lower()
