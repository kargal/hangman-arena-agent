# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/). Minor versions track arena seasons.

## [Unreleased]

## [0.3.2] - 2026-10-21

### Changed
- Live standings are printed as their own block after every finished puzzle: a header, the server's one-line
  notice on where you stand (`standings.notice`, from hangman-arena 0.3.2) and the table, set off by blank lines.
- `--json`: the `standings` object is moved up right after `result`, with `notice` as its first field (contents
  unchanged).
- CLAUDE.md and README: a "Live standings" section on what the standings show and how to use them;
  `docs/protocol.md` documents `notice`.

## [0.3.1] - 2026-10-21

### Added
- Live standings: after every finished puzzle the CLI prints the current season's standings (rank, entry,
  puzzles completed, average guesses so far), as returned by the server in the puzzle-end response.
- `arena standings` and `ArenaClient.standings()` (`GET /v1/sessions/{id}/standings`); `--json` passes the
  `standings` object through unchanged.
- `docs/protocol.md` documents the `Standings` object and the new endpoint.

## [0.3.0] - 2026-10-09 — Season 3

### Added
- `arena status` prints a running average for the session.
- Low-budget warning when five or fewer guesses remain on a puzzle.
- `learning_curve()` helper and first/second-half averages in `SessionStats`.
- Difficulty-adjusted learning slope: `Puzzle.reference_guesses`, `excess_guesses()`,
  `difficulty_adjusted_slope()`, and `average_excess_guesses` / `difficulty_adjusted_slope` in `SessionStats`.
  Season 3 serves puzzles in order of increasing difficulty, so in-context learning is measured relative to
  each puzzle's reference difficulty.
- `docs/protocol.md` documents `average_guesses` on the session object.

### Changed
- `word_lengths` now counts hidden letters only, so `"Don't"` reports 4.
- Typographic quotes and dashes are folded to ASCII before solve attempts are compared.

## [0.2.0] - 2026-08-27 — Season 2

### Added
- Multi-word phrases: spaces and punctuation are shown, solve attempts are whitespace-insensitive.
- `arena history` and `GET /v1/sessions/{id}/history`.
- `--json` flag on every CLI command.
- Learning-curve slope in session summaries.

### Changed
- Guess budget raised from 26 to 30 per puzzle; forfeits are scored as 30.
- Repeated letters are rejected with `repeated_guess` instead of being silently charged.

## [0.1.0] - 2026-08-04 — Season 1 (pilot)

### Added
- `hangman_engine`: masking, letter/solve judging, per-puzzle scoring.
- `arena_client`: `ArenaClient` SDK and the `arena` CLI (`next`, `guess`, `solve`, `status`).

[Unreleased]: https://github.com/kargal/hangman-arena-agent/compare/v0.3.2...HEAD
[0.3.2]: https://github.com/kargal/hangman-arena-agent/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/kargal/hangman-arena-agent/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/kargal/hangman-arena-agent/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/kargal/hangman-arena-agent/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kargal/hangman-arena-agent/releases/tag/v0.1.0
