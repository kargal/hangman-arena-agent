# hangman-arena-agent

[![CI](https://github.com/kargal/hangman-arena-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/kargal/hangman-arena-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%E2%80%933.12-blue)
![Season](https://img.shields.io/badge/season-2-orange)

**The agent workspace for [Hangman Arena](https://github.com/kargal/hangman-arena)** — a benchmark that
measures how efficiently LLM agents solve hangman puzzles, and how much they improve over consecutive puzzles
within a single session.

Agents evaluated in Hangman Arena are launched **inside this repository**. It contains everything an agent needs
to play:

| Path | What it is |
| --- | --- |
| [`arena_client/`](arena_client/) | the `arena` command-line tool and a small Python SDK (`ArenaClient`) |
| [`hangman_engine/`](hangman_engine/) | the game rules: masking, guess judging, scoring — the exact code the server uses |
| [`docs/protocol.md`](docs/protocol.md) | the HTTP API spoken between client and server |
| [`CLAUDE.md`](CLAUDE.md) | quick-start notes for Claude Code |

The server, puzzle bank, season configs, runner and leaderboard live in the
[**hangman-arena**](https://github.com/kargal/hangman-arena) repository. That repository is maintained
separately by the benchmark maintainers and is not part of the agent workspace.

---

## How a session works

An agent plays one **session** of **20 puzzles** back-to-back, in a single context. Puzzles are English words
and common multi-word phrases (idioms, titles, place names, …), each with a category hint.

1. `arena next` reveals the next puzzle as a mask, e.g. `_ _ _ _ _ _ (6 letters)`.
2. The agent guesses letters (`arena guess e`) or tries the whole answer (`arena solve "..."`).
3. The puzzle ends when every letter is revealed, a solve attempt is correct, or the guess budget runs out.
4. Repeat until all 20 puzzles are done.

Every session in a season sees the **same 20 puzzles in the same order**, so results are directly comparable
across agents.

## Rules

* Only the letters **A–Z** are hidden. Spaces, hyphens, apostrophes and other punctuation are shown from the
  start.
* Each **letter guess** costs **1 guess**, whether or not the letter is in the answer.
* Each **solve attempt** costs **1 guess**. Solve attempts are case- and whitespace-insensitive
  (`"rock  AND roll"` matches `ROCK AND ROLL`); punctuation must match what the mask shows.
* Repeating a letter you have already guessed is **rejected and not counted**. Malformed input (`ab`, `7`,
  empty solve) is likewise rejected without cost.
* Revealing every letter solves the puzzle automatically — no final solve attempt is needed.
* The budget is **30 guesses per puzzle**. A puzzle that is not solved within 30 guesses is **forfeited** and
  scored as 30.
* You can only move on with `arena next` once the current puzzle is solved or forfeited. Puzzles cannot be
  skipped.

## Metrics

| Metric | Definition | Better |
| --- | --- | --- |
| **Avg. guesses / puzzle** (primary) | mean over the 20 puzzles of guesses used (forfeit = 30) | lower |
| **Learning-curve slope** | OLS slope of guesses vs. round index 1…20 | more negative |
| Solve rate | fraction of puzzles solved within budget | higher |

The learning curve captures *in-context learning*: whether an agent gets better at the game — and at the
season's puzzle style — as the session goes on. Both metrics are computed by
[`hangman_engine/scoring.py`](hangman_engine/scoring.py); the leaderboard is published in the
[arena repository](https://github.com/kargal/hangman-arena#leaderboard).

## Using the `arena` CLI

The arena runner sets three environment variables before the agent starts:

| Variable | Meaning | Default |
| --- | --- | --- |
| `ARENA_URL` | arena server base URL | `http://arena:8080` |
| `ARENA_TOKEN` | bearer token for this session | — |
| `ARENA_SESSION` | session id | — |

```console
$ arena next
Puzzle 1/20 [s2-1712] category: Around the House
_ _ _ _ _ _ _ _ (8 letters)
guesses: 0  misses: 0

$ arena guess e
'E' is in the answer (1 position)
_ E _ _ _ _ _ _ (8 letters)
guesses: 1  misses: 0

$ arena guess r
'R' is not in the answer
_ E _ _ _ _ _ _ (8 letters)
guesses: 2  misses: 1 (R)

$ arena solve "teaspoon"
Correct!
T E A S P O O N (8 letters)
guesses: 3  misses: 1 (R)
Solved! Answer: TEASPOON - 3 guesses
Run `arena next` for puzzle 2/20.
```

Other commands:

```console
$ arena status     # session progress + current puzzle
$ arena history    # finished puzzles with answers and guess counts
$ arena --json guess t   # raw JSON response (any command)
```

Exit status is `0` on success, `1` if the server rejected the request (e.g. a repeated letter, or `arena next`
while a puzzle is still in progress), and `2` for configuration errors.

### Python SDK

```python
from arena_client import ArenaClient

with ArenaClient.from_env() as arena:
    puzzle = arena.next_puzzle()["puzzle"]
    print(puzzle["mask"], puzzle["category"])
    arena.guess("e")
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check . && mypy
```

The engine has no third-party dependencies; the client depends only on `httpx`.

Changes to `hangman_engine` change the rules of the game, so they are released together with a new arena
season. See [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
