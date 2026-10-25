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
uv run src/mini_calude_code/step1.py
```

## Steps

- **Step 1:** send a single prompt to an LLM and print the reply.
