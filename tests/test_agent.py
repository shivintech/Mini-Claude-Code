import copy
import json
import os
from types import SimpleNamespace

import pytest

from mini_calude_code import agent, step1


def tool_call(call_id, name, args):
    arguments = args if isinstance(args, str) else json.dumps(args)
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=arguments))


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


# --- tools ---

def test_list_files_marks_folders(tmp_path):
    (tmp_path / "b.txt").write_text("", encoding="utf-8")
    (tmp_path / "a_dir").mkdir()

    assert agent.list_files(str(tmp_path)) == "a_dir/\nb.txt"


def test_list_files_empty_directory(tmp_path):
    assert agent.list_files(str(tmp_path)) == "(empty directory)"


def test_write_then_read_file(tmp_path):
    path = str(tmp_path / "hello.txt")

    assert agent.write_file(path, "hi there") == f"Saved {path} (8 characters)"
    assert agent.read_file(path) == "hi there"


def test_run_command_declined_does_not_run(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    monkeypatch.setattr(agent.subprocess, "run", lambda *a, **k: pytest.fail("command should not run"))

    assert agent.run_command("echo hi") == "The user declined to run this command."


def test_run_command_approved_returns_output(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "y")

    assert agent.run_command("echo hi") == "hi"


# --- run_tool ---

def test_run_tool_unknown_name():
    assert agent.run_tool(tool_call("c1", "delete_everything", {})) == "Error: unknown tool delete_everything"


def test_run_tool_reports_errors_instead_of_crashing(tmp_path):
    missing = str(tmp_path / "missing.txt")

    result = agent.run_tool(tool_call("c1", "read_file", {"path": missing}))

    assert result.startswith("Error:")


def test_run_tool_bad_json_arguments():
    assert agent.run_tool(tool_call("c1", "read_file", "not json")).startswith("Error:")


# --- run_agent ---

def test_run_agent_answers_without_tools():
    client, completions = fake_client(reply("Hello!"))
    messages = [{"role": "system", "content": agent.SYSTEM_PROMPT}, {"role": "user", "content": "Hi"}]

    assert agent.run_agent(client, messages) == "Hello!"
    assert completions.calls[0]["tools"] == agent.TOOL_SCHEMAS
    assert messages[-1] == {"role": "assistant", "content": "Hello!"}


def test_run_agent_runs_tools_and_sends_results_back(tmp_path):
    path = str(tmp_path / "out.txt")
    client, completions = fake_client(
        reply(tool_calls=[tool_call("c1", "write_file", {"path": path, "content": "done"})]),
        reply(tool_calls=[tool_call("c2", "read_file", {"path": path})]),
        reply("Wrote and checked out.txt."),
    )
    messages = [{"role": "user", "content": "Write done to out.txt and check it"}]

    answer = agent.run_agent(client, messages)

    assert answer == "Wrote and checked out.txt."
    assert len(completions.calls) == 3
    last_request = completions.calls[2]["messages"]
    tool_results = [m for m in last_request if m["role"] == "tool"]
    assert tool_results[0]["tool_call_id"] == "c1"
    assert tool_results[1] == {"role": "tool", "tool_call_id": "c2", "content": "done"}


@pytest.mark.skipif(not os.environ.get("RUN_LIVE_TESTS"), reason="set RUN_LIVE_TESTS=1 to call the real Groq API")
def test_run_agent_live_writes_file(tmp_path):
    path = tmp_path / "greeting.txt"
    messages = [
        {"role": "system", "content": agent.SYSTEM_PROMPT},
        {"role": "user", "content": f"Create the file {path} containing exactly the text: hello agent"},
    ]

    agent.run_agent(step1.make_client(), messages)

    assert path.read_text(encoding="utf-8").strip() == "hello agent"
