"""Scoring: guesses per puzzle, session aggregates and learning curves.

The primary metric is **average guesses per puzzle** over a session (lower is
better). Forfeited puzzles count as :data:`~hangman_engine.puzzle.MAX_GUESSES`.

Puzzles in a session are served in order of increasing difficulty, so the raw
trend of guesses over the session mostly reflects the puzzles, not the agent.
In-context learning is therefore measured **relative to puzzle difficulty**:
each puzzle carries a calibrated *reference difficulty* (expected guesses for a
fixed reference player), and the **difficulty-adjusted learning slope** is the
ordinary least-squares slope of *excess guesses* (score minus reference) against
round index (1, 2, ..., n). A negative slope means the agent did increasingly
better than the reference as the session went on.

The raw :func:`learning_curve_slope` (score vs. round index) is still reported
for reference.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

from hangman_engine.puzzle import PuzzleState, PuzzleStatus


def puzzle_score(state: PuzzleState) -> int:
    """Score of a finished puzzle (guesses used, or the cap if forfeited)."""
    score = state.score
    if score is None:
        raise ValueError(f"puzzle {state.puzzle.puzzle_id} is not finished")
    return score


def learning_curve(scores: Sequence[float]) -> list[tuple[int, float]]:
    """``[(round_index, score), ...]`` with 1-based round indices."""
    return [(i, float(s)) for i, s in enumerate(scores, start=1)]


def learning_curve_slope(scores: Sequence[float]) -> float | None:
    """OLS slope of score vs. round index; ``None`` for fewer than 2 rounds."""
    n = len(scores)
    if n < 2:
        return None
    xs = range(1, n + 1)
    mean_x = (n + 1) / 2
    mean_y = sum(scores) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, scores, strict=True))
    return sxy / sxx


def excess_guesses(scores: Sequence[float], references: Sequence[float | None]) -> list[float] | None:
    """Per-puzzle ``score - reference``; ``None`` if any reference is missing."""
    if len(scores) != len(references):
        raise ValueError("scores and references must have the same length")
    if any(r is None for r in references):
        return None
    return [float(s) - float(r) for s, r in zip(scores, references, strict=True) if r is not None]


def difficulty_adjusted_slope(scores: Sequence[float], references: Sequence[float | None]) -> float | None:
    """OLS slope of excess guesses (score minus reference difficulty) vs. round index.

    ``None`` for fewer than 2 rounds or if any puzzle has no reference difficulty.
    """
    excess = excess_guesses(scores, references)
    return None if excess is None else learning_curve_slope(excess)


@dataclass(frozen=True)
class SessionStats:
    puzzles: int
    solved: int
    forfeited: int
    total_guesses: int
    average_guesses: float | None
    median_guesses: float | None
    learning_curve_slope: float | None
    first_half_average: float | None
    second_half_average: float | None
    average_excess_guesses: float | None
    difficulty_adjusted_slope: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _mean(values: Sequence[float]) -> float | None:
    return statistics.fmean(values) if values else None


def summarize(states: Sequence[PuzzleState]) -> SessionStats:
    """Aggregate statistics over the *finished* puzzles in ``states``."""
    finished = [s for s in states if s.finished]
    scores = [puzzle_score(s) for s in finished]
    excess = excess_guesses(scores, [s.puzzle.reference_guesses for s in finished])
    half = len(scores) // 2
    return SessionStats(
        puzzles=len(finished),
        solved=sum(1 for s in finished if s.status is PuzzleStatus.SOLVED),
        forfeited=sum(1 for s in finished if s.status is PuzzleStatus.FORFEITED),
        total_guesses=sum(scores),
        average_guesses=_mean(scores),
        median_guesses=statistics.median(scores) if scores else None,
        learning_curve_slope=learning_curve_slope(scores),
        first_half_average=_mean(scores[:half]) if half else None,
        second_half_average=_mean(scores[half:]) if half else None,
        average_excess_guesses=_mean(excess) if excess else None,
        difficulty_adjusted_slope=learning_curve_slope(excess) if excess is not None else None,
    )
