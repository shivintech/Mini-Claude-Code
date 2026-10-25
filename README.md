# Mini Claude Code

Building an AI agent from scratch.

A step-by-step project to build a small coding agent, inspired by Claude Code, in Python.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
```

Create a `.env` file in the project root with your API key (it is git-ignored):

```
GROQ_API_KEY=your-key-here
```

Get a free key at https://console.groq.com/keys.

## Run

```sh
uv run src/mini_calude_code/step1.py   # one question, one answer
uv run src/mini_calude_code/step2.py   # chat in the terminal; type exit to quit
uv run src/mini_calude_code/step3.py   # the model reads files using a tool
uv run src/mini_calude_code/agent.py   # coding agent: list, read, write files and run commands
```

Run these from the project root: steps 3 and 4 resolve file paths relative to where you run them.

## Test

```sh
uv run pytest
```

Tests use a fake client, so they need no API key. To also call the real Groq API, set `RUN_LIVE_TESTS=1`.

## Steps

- **Step 1:** send a single prompt to an LLM and print the reply.
- **Step 2:** a chat loop that remembers the conversation.
- **Step 3:** give the model a tool (`read_file`) and loop until it is done using it.
- **Step 4:** a small coding agent (`agent.py`) that can list, read and write files and run shell commands.

### Step 2: why agents need to remember context

An LLM API is **stateless**. Each request is answered on its own, and the model
keeps no memory of earlier requests. If you tell it your name in one call and ask
for it in the next, it has no idea, because it never saw the first message.

So the "memory" has to live in our program. Step 2 keeps a `messages` list and,
on every turn:

1. appends what you typed as a `user` message,
2. sends the **entire list** to the model,
3. appends the model's reply as an `assistant` message.

```
Turn 1 sends:  [user: "My name is Shivin"]
Turn 2 sends:  [user: "My name is Shivin", assistant: "Hi Shivin!", user: "What is my name?"]
```

Because turn 2 includes the earlier messages, the model can answer "Shivin".

This is the foundation of an agent. A coding agent like Claude Code works over many
steps (read a file, run a command, fix an error), and each step only makes sense
with what came before. Later steps will add tool calls and their results to this
same list.

The trade-off is that the history grows every turn, so each request sends more
tokens. Real agents eventually have to trim or summarise old messages to stay
within the model's context window.

### Step 3: tools and the agent loop

A chatbot can only talk. An **agent** can act. Step 3 is where that starts: we give
the model a tool, `read_file`, so it can look at files on disk.

The model never runs code itself. Instead:

1. We send the conversation plus a **tool schema**: a JSON description of each tool's
   name, purpose and parameters.
2. If the model needs a tool, it replies with a **tool call** (e.g.
   `read_file(path="notes.txt")`) instead of an answer.
3. **Our program** runs the function and appends the result to `messages` as a
   `tool` message, matched to the request by its `tool_call_id`.
4. We call the model again with the updated history.
5. Repeat until the model replies with no tool calls. That reply is the final answer.

```
user:       What is inside notes.txt, notes1.txt and notes2.txt?
assistant:  [tool calls] read_file(notes.txt), read_file(notes1.txt), read_file(notes2.txt)
tool:       This is a dummy file. Hello Shivin!!
tool:       File notes1.txt not found
tool:       File notes2.txt not found
assistant:  notes.txt says "Hello Shivin!!"; notes1.txt and notes2.txt don't exist.
```

This loop (model decides, program acts, result goes back into the history) is the
core of every coding agent, including Claude Code. It relies on step 2's memory: the
tool results only help because they are in the history the model sees next.

Tools are looked up by name in a `TOOLS` table, so adding one (writing files,
running commands) means writing the function and its schema. Unknown tool names
return an error message to the model instead of crashing the program.

### Step 4: a coding agent

Step 4 keeps step 3's loop and gives the model enough tools to do real work in a
project folder:

| Tool | What it does |
| --- | --- |
| `list_files(path)` | lists a directory; folders end with `/` |
| `read_file(path)` | returns a file's contents |
| `write_file(path, content)` | creates or overwrites a file |
| `run_command(command)` | runs a shell command and returns its output |

With these the model can look around, make a change, and check it, for example
by writing a script and then running it to see if it works.

```
You:    Create hello.py that prints hi, then run it
  tool: write_file({'path': 'hello.py', 'content': "print('hi')"})
  Run 'python hello.py'? [y/N] y
  tool: run_command({'command': 'python hello.py'})
Agent:  I created hello.py and ran it; it printed "hi".
```

Running commands is the most dangerous tool, so `run_command` asks you to approve
each command first. If you decline, the model is told so and can try something
else. This is the same idea as Claude Code's permission prompts.

Two other details make the agent more robust:

- **Errors go back to the model.** If a tool fails (a missing file, bad arguments),
  `run_tool` returns the error as text instead of crashing, so the model can read
  it and fix its next step.
- **The system prompt names the OS.** The model is told which operating system it
  is on, so it picks shell commands that work there (e.g. `dir` vs `ls`).

The chat in `main()` keeps one `messages` list across turns, so you can give
follow-up instructions and the agent remembers what it already did.
