# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/). Minor versions track arena seasons.

## [Unreleased]

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

[Unreleased]: https://github.com/kargal/hangman-arena-agent/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/kargal/hangman-arena-agent/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/kargal/hangman-arena-agent/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kargal/hangman-arena-agent/releases/tag/v0.1.0
