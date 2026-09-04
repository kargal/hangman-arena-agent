# CLAUDE.md

Notes for Claude Code when working in this repository.

## What this repository is

This is the agent workspace for **Hangman Arena** (Season 2). You play hangman puzzles against the arena server
using the `arena` command-line tool, which is already installed in this environment and configured through the
`ARENA_URL`, `ARENA_TOKEN` and `ARENA_SESSION` environment variables.

A session is 20 puzzles played in order. Your score is the **average number of guesses per puzzle** — lower is
better.

## Commands

```bash
arena next              # start the next puzzle (only once the current one is finished)
arena guess <letter>    # guess one letter, e.g. `arena guess e`
arena solve "<answer>"  # attempt the full answer, e.g. `arena solve "rock and roll"`
arena status            # current puzzle and session progress
arena history           # finished puzzles with answers and guess counts
```

Add `--json` before the command (`arena --json status`) for machine-readable output.

## Rules (summary)

- Letters A–Z are hidden; spaces, hyphens and apostrophes are shown.
- Every letter guess and every solve attempt counts as one guess.
- Repeated letters and malformed guesses are rejected and not counted.
- Revealing all letters solves the puzzle; a correct solve attempt also solves it.
- Solve attempts are case- and whitespace-insensitive.
- 30 guesses per puzzle at most; an unsolved puzzle is forfeited and scored as 30.
- Puzzles cannot be skipped: `arena next` only works after the current puzzle is solved or forfeited.

Full rules: [README.md](README.md#rules). API details: [docs/protocol.md](docs/protocol.md).

## Where scores come from

The arena server judges every guess with the code in `hangman_engine/` and records the result. The score for a
puzzle is the number of guesses the server counted (30 if forfeited); the session score is the mean over all
20 puzzles. `arena history` shows the per-puzzle numbers the server has recorded so far.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check . && mypy
```
