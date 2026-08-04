import math

import pytest

from hangman_engine import (
    MAX_GUESSES,
    Puzzle,
    PuzzleState,
    difficulty_adjusted_slope,
    excess_guesses,
    learning_curve,
    learning_curve_slope,
    puzzle_score,
    summarize,
)


def solved_in(n: int, answer: str = "oxbow", reference: float | None = None) -> PuzzleState:
    state = PuzzleState(Puzzle(f"t-{n:04d}", answer, "Test", reference_guesses=reference))
    for i in range(n - 1):
        state.solve(f"miss {i}")
    state.solve(answer)
    return state


def forfeited() -> PuzzleState:
    state = PuzzleState(Puzzle("t-9999", "oxbow", "Test"))
    state.forfeit()
    return state


def test_puzzle_score() -> None:
    assert puzzle_score(solved_in(7)) == 7
    assert puzzle_score(forfeited()) == MAX_GUESSES


def test_puzzle_score_requires_finished_puzzle() -> None:
    with pytest.raises(ValueError):
        puzzle_score(PuzzleState(Puzzle("t-0001", "oxbow", "Test")))


def test_learning_curve_indices_are_one_based() -> None:
    assert learning_curve([5, 4]) == [(1, 5.0), (2, 4.0)]


def test_slope_of_perfect_improvement() -> None:
    slope = learning_curve_slope([10, 9, 8, 7, 6])
    assert slope is not None and math.isclose(slope, -1.0)


def test_slope_of_flat_curve_is_zero() -> None:
    assert learning_curve_slope([8, 8, 8]) == 0.0


def test_slope_needs_two_points() -> None:
    assert learning_curve_slope([]) is None
    assert learning_curve_slope([5]) is None


def test_excess_guesses() -> None:
    assert excess_guesses([4, 9], [2.5, 10.0]) == [1.5, -1.0]
    assert excess_guesses([4, 9], [2.5, None]) is None
    with pytest.raises(ValueError):
        excess_guesses([4], [2.5, 3.0])


def test_adjusted_slope_removes_the_difficulty_ramp() -> None:
    # guesses grow exactly as fast as the puzzles get harder: no learning
    references = [2.0, 4.0, 6.0, 8.0]
    scores = [3, 5, 7, 9]
    assert learning_curve_slope(scores) == pytest.approx(2.0)
    assert difficulty_adjusted_slope(scores, references) == pytest.approx(0.0)


def test_adjusted_slope_detects_improvement_on_harder_puzzles() -> None:
    references = [2.0, 4.0, 6.0, 8.0]
    scores = [5, 6, 7, 8]  # excess 3, 2, 1, 0
    assert learning_curve_slope(scores) == pytest.approx(1.0)
    assert difficulty_adjusted_slope(scores, references) == pytest.approx(-1.0)


def test_adjusted_slope_needs_references_and_two_points() -> None:
    assert difficulty_adjusted_slope([3, 4], [1.0, None]) is None
    assert difficulty_adjusted_slope([3], [1.0]) is None


def test_summarize_session() -> None:
    states = [solved_in(10), solved_in(8), forfeited(), solved_in(4)]
    stats = summarize(states)
    assert stats.puzzles == 4
    assert stats.solved == 3
    assert stats.forfeited == 1
    assert stats.total_guesses == 10 + 8 + 30 + 4
    assert stats.average_guesses == pytest.approx(13.0)
    assert stats.median_guesses == 9.0
    assert stats.first_half_average == pytest.approx(9.0)
    assert stats.second_half_average == pytest.approx(17.0)
    assert stats.to_dict()["solved"] == 3
    # no reference difficulties -> no adjusted metrics
    assert stats.average_excess_guesses is None
    assert stats.difficulty_adjusted_slope is None


def test_summarize_with_reference_difficulty() -> None:
    states = [solved_in(4, reference=2.0), solved_in(5, reference=4.0), solved_in(6, reference=6.0)]
    stats = summarize(states)
    assert stats.average_excess_guesses == pytest.approx(1.0)
    assert stats.difficulty_adjusted_slope == pytest.approx(-1.0)
    assert stats.learning_curve_slope == pytest.approx(1.0)


def test_summarize_ignores_unfinished_puzzles() -> None:
    states = [solved_in(6), PuzzleState(Puzzle("t-0005", "oxbow", "Test"))]
    assert summarize(states).puzzles == 1


def test_summarize_empty_session() -> None:
    stats = summarize([])
    assert stats.puzzles == 0
    assert stats.average_guesses is None
    assert stats.learning_curve_slope is None
    assert stats.difficulty_adjusted_slope is None
