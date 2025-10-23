Python AI Agent
================

What this is
------------
This repository is a small, focused project that demonstrates an agent-style workflow: a local Python program can call out to a language model, let the model plan function calls, and then safely execute those calls locally (for example: listing files, reading files, running Python scripts, writing files). The project is intentionally small so it is easy to inspect, test, and iterate.

High-level components
---------------------
- `main.py` — CLI entry point and orchestration. It sends user prompts to the model, runs a small tool-invocation loop that executes requested functions, and then prints the model's final response.
- `functions/` — Local function implementations and helper utilities that the model can request: 
  - `get_files_info.py` — list directory contents (guarded to a working directory)
  - `get_file_content.py` — read file contents with truncation safeguards
  - `run_python_file.py` — run Python files with captured stdout/stderr
  - `write_file.py` — write or overwrite files (guarded to a working directory)
  - `call_function.py` — adapter that maps model function-calls to local function calls and wraps the results for the model
  - `schemas.py` — aggregates function schemas (declarations) used to tell the model how to call local functions
  - `config.py` — small configuration constants (e.g. MAX_FILE_CHARS)
- `calculator/` — a small example app used as a target for the agent to inspect and operate against (contains a tiny calculator app and tests)
- `tests.py` — a set of quick manual tests to exercise the functions locally (CLI runner)

Why this layout
----------------
Keeping function implementations next to their schema/declarations makes it easy to maintain and reason about each tool. `main.py` intentionally keeps orchestration logic separate so the fns can be re-used or tested in isolation.

Quickstart — running the CLI locally
-----------------------------------
1. Create and activate a virtual environment (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # if you have one
```

2. Set your model/API key in the environment; for example (bash):

```bash
export GEMINI_API_KEY="your_api_key_here"
```

3. Ask the agent a prompt. Example:

```bash
python3 main.py "list the files in the pkg directory" --verbose
```

Token counts and verbose output
-------------------------------
- The agent prints token usage summary when the `--verbose` flag is used. The counts are taken from the model's usage metadata and displayed as:

  Prompt tokens: X

  Response tokens: Y

- Use `--verbose` during development to see the prompt and token usage for each generation iteration. This helps estimate cost and debug long conversations.

Developer checklist before pushing
---------------------------------
- Run the quick tests: `python3 tests.py` and inspect any failures before committing.
- Use `--verbose` when running `main.py` locally to verify function-invocation flows.
- Review `functions/` implementations before allowing remote pushes; these functions are intentionally powerful and can modify files or execute code inside the `calculator/` working directory.

Committing and pushing changes
-----------------------------
This repository doesn't perform any automatic remote pushes. To commit locally and push to a remote follow these steps (example):

1. Stage files:

  git add README.md

2. Commit with a clear message:

  git commit -m "docs: expand README with token-counts, verbose notes, and push checklist"

3. Push to your fork/branch:

  git push origin your-branch-name

If you want me to create the commit here, I can stage and commit the README locally and then wait for your confirmation before pushing to the remote.

Notes
-----
- The project purposely enforces a `working_directory` (typically `./calculator`) when tools are invoked. This prevents accidental reads/writes outside the permitted area.
- Reading a file longer than the configured `MAX_FILE_CHARS` will truncate the result and append a short marker describing the truncation.
- Running Python files uses `subprocess.run` with a timeout (30s) and captures both stdout and stderr so the model (or the developer) can inspect the results safely.

Developer notes
---------------
- The tool-invocation loop in `main.py` sends the full conversation every turn so the model can plan a function call, the code executes the call and appends the function result to the conversation, and the model can then respond with a final answer.
- If you need to debug the model/tool flow, use the `--verbose` flag to print calls and function results.
- Be careful when testing `write_file` and `run_python_file` — they are powerful and will modify files or execute scripts. The agent intentionally restricts operations to the `calculator` directory, but review changes before pushing them.

Testing
-------
- There is a lightweight `tests.py` harness at the repository root that runs quick checks for the helper functions. Run it with:

```bash
python3 tests.py
```

If you want more formal tests, consider adding pytest-based tests that mock the model responses and assert the tool-invocation loop behaves as expected.

Contributing
------------
If you make changes, please:

1. Run the quick tests: `python3 tests.py`
2. Commit logically grouped changes with a clear commit message
3. Push to your fork/branch and open a PR

License
-------
This project is intended as an educational sample. Add a license file if you plan to open-source it publicly.

If you'd like, I can also:
- Run the local test harness and paste the output here
- Add inline documentation/docstrings to each function file
- Run the `git add`/`git commit`/`git push` so the README is saved to your remote
