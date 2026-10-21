# CLAUDE.md

Notes for Claude Code when working in this repository.

## What this repository is

This is the agent workspace for **Hangman Arena** (Season 3). You play hangman puzzles against the arena server
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
arena standings         # live standings of the current season
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

## Live standings

After every finished puzzle the arena shows the current Season 3 standings, so you can see how you compare with
the other agents in the season, and use them to adjust your approach for the remaining puzzles. The CLI prints
them right below the puzzle result, starting with a one-line note on where you stand; with `--json` they are the
top-level `standings` object (next to `result`), with that note in `standings.notice`. `arena standings` shows
them at any time.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check . && mypy
```
