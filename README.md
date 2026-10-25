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
```

## Test

```sh
uv run pytest
```

Tests use a fake client, so they need no API key. To also call the real Groq API, set `RUN_LIVE_TESTS=1`.

## Steps

- **Step 1:** send a single prompt to an LLM and print the reply.
- **Step 2:** a chat loop that remembers the conversation.

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
