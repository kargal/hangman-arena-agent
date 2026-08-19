# Hangman Arena HTTP protocol (v1)

This document describes the API between the `arena` client and the arena server
([hangman-arena](https://github.com/kargal/hangman-arena)). The reference client is
[`arena_client/client.py`](../arena_client/client.py).

* Base URL: `ARENA_URL` (default `http://arena:8080`). All endpoints are under `/v1`.
* Requests and responses are JSON (`Content-Type: application/json`).
* Session endpoints require `Authorization: Bearer <ARENA_TOKEN>`. A token is valid for exactly one session.

## Objects

### `Session`

Progress of a session. Never contains answers of unfinished puzzles.

```json
{
  "session_id": "ses_4f1c2a9b0e7d3c11",
  "season": 2,
  "total": 20,
  "completed": 2,
  "current_index": 3,
  "finished": false,
  "agent": "claude_code",
  "model": "claude-opus-5",
  "created_at": "2026-10-14T09:12:44Z"
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `completed` | int | puzzles solved or forfeited |
| `current_index` | int | 1-based index of the current (or most recent) puzzle; `0` before the first `next` |
| `finished` | bool | `true` once all `total` puzzles are finished |

### `Puzzle`

```json
{
  "index": 3,
  "total": 20,
  "puzzle_id": "s2-1712",
  "category": "Around the House",
  "type": "word",
  "mask": "_E______",
  "word_lengths": [8],
  "letters": 8,
  "status": "in_progress",
  "guesses": 2,
  "max_guesses": 30,
  "guessed_letters": ["E", "R"],
  "missed_letters": ["R"],
  "solve_attempts": [],
  "answer": null,
  "score": null
}
```

| Field | Type | Notes |
| --- | --- | --- |
| `type` | `"word"` \| `"phrase"` | phrases contain spaces |
| `mask` | string | hidden letters are `_`; spaces and punctuation are shown verbatim |
| `word_lengths` | int[] | number of hidden letters in each space-separated word |
| `status` | `"in_progress"` \| `"solved"` \| `"forfeited"` | |
| `guesses` | int | guesses charged so far (letters + solve attempts) |
| `answer` | string \| null | upper-case answer, **only once the puzzle is finished** |
| `score` | int \| null | guesses charged for the puzzle (30 if forfeited), once finished |

### `GuessResult`

```json
{"kind": "letter", "value": "E", "correct": true, "occurrences": 1, "status": "in_progress", "guesses": 1}
```

`kind` is `"letter"` or `"solve"`. For solves, `value` is the normalised attempt and `occurrences` is `0`.

### Errors

Errors use a uniform envelope:

```json
{"error": {"code": "repeated_guess", "message": "letter 'E' was already guessed (not counted)"}}
```

| HTTP | `code` | When |
| --- | --- | --- |
| 400 | `invalid_guess` | not a single letter A–Z, or an empty solve attempt |
| 401 | `unauthorized` | missing/invalid token, or token for another session |
| 404 | `session_not_found` | unknown session id |
| 409 | `repeated_guess` | letter already guessed in this puzzle (not counted) |
| 409 | `puzzle_in_progress` | `next` while the current puzzle is unfinished |
| 409 | `no_active_puzzle` | `guess`/`solve` before the first `next`, or after the puzzle finished |
| 409 | `session_complete` | `next` after the last puzzle |
| 422 | `bad_request` | malformed JSON body |

Rejected requests never change the puzzle state and never cost a guess.

## Endpoints

### `GET /v1/sessions/{session_id}`

Returns `{"session": Session, "puzzle": Puzzle | null}` — the current (or most recently finished) puzzle.

### `POST /v1/sessions/{session_id}/next`

Starts the next puzzle in the season schedule. Returns `{"session": Session, "puzzle": Puzzle}`.

### `POST /v1/sessions/{session_id}/guess`

Body: `{"letter": "e"}`. Returns `{"session": Session, "puzzle": Puzzle, "result": GuessResult}`, plus
`"summary"` (see below) if this guess finished the session.

### `POST /v1/sessions/{session_id}/solve`

Body: `{"answer": "teaspoon"}`. Same response shape as `guess`.

### `GET /v1/sessions/{session_id}/history`

Returns `{"session": Session, "puzzles": [Puzzle, ...]}` with every **finished** puzzle in order, including
answers and scores.

### `GET /v1/sessions/{session_id}/summary`

```json
{
  "session": { "...": "..." },
  "scores": [7, 12, 9],
  "summary": {
    "puzzles": 3,
    "solved": 3,
    "forfeited": 0,
    "total_guesses": 28,
    "average_guesses": 9.333,
    "median_guesses": 9,
    "learning_curve_slope": 1.0
  }
}
```

`summary` fields are produced by `hangman_engine.scoring.summarize` over finished puzzles.

### Administrative endpoints

Session creation (`POST /v1/sessions`) and listing require the server's admin token and are used by the arena
runner only. They are documented in the arena repository.

## Versioning

The API is versioned by path prefix. Fields may be added within `v1`; clients must ignore unknown fields.
