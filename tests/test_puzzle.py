import pytest

from hangman_engine import (
    MAX_GUESSES,
    InvalidGuessError,
    Puzzle,
    PuzzleFinishedError,
    PuzzleState,
    PuzzleStatus,
    RepeatedGuessError,
)


def make(answer: str = "teaspoon", kind: str = "word", **kwargs: int) -> PuzzleState:
    return PuzzleState(Puzzle("t-0001", answer, "Around the House", kind), **kwargs)


def test_initial_state() -> None:
    state = make()
    assert state.mask == "________"
    assert state.guesses == 0
    assert state.status is PuzzleStatus.IN_PROGRESS
    assert state.score is None
    assert state.view()["answer"] is None


def test_correct_letter_reveals_all_occurrences() -> None:
    state = make()
    result = state.guess_letter("o")
    assert result.correct and result.occurrences == 2
    assert state.mask == "_____OO_"
    assert state.guesses == 1


def test_missed_letter_is_counted() -> None:
    state = make()
    result = state.guess_letter("z")
    assert not result.correct and result.occurrences == 0
    assert state.missed_letters == ["Z"]
    assert state.guesses == 1


def test_repeated_letter_is_rejected_and_not_counted() -> None:
    state = make()
    state.guess_letter("e")
    with pytest.raises(RepeatedGuessError):
        state.guess_letter("E")
    state.guess_letter("z")
    with pytest.raises(RepeatedGuessError):
        state.guess_letter("z")
    assert state.guesses == 2


def test_invalid_letter_is_not_counted() -> None:
    state = make()
    with pytest.raises(InvalidGuessError):
        state.guess_letter("ea")
    assert state.guesses == 0


def test_revealing_every_letter_solves_the_puzzle() -> None:
    state = make("oxbow")
    for letter in "oxbw":
        state.guess_letter(letter)
    assert state.status is PuzzleStatus.SOLVED
    assert state.score == 4
    assert state.view()["answer"] == "OXBOW"


def test_solve_is_case_and_whitespace_insensitive() -> None:
    state = make("Rock and roll", kind="phrase")
    result = state.solve("  rOCK   AND roll ")
    assert result.correct
    assert state.status is PuzzleStatus.SOLVED
    assert state.score == 1
    assert state.mask == "ROCK AND ROLL"


def test_wrong_solve_costs_one_guess() -> None:
    state = make()
    result = state.solve("teaspoons")
    assert not result.correct
    assert state.guesses == 1
    assert state.solve_attempts == ["TEASPOONS"]
    assert state.status is PuzzleStatus.IN_PROGRESS


def test_solve_requires_matching_punctuation() -> None:
    state = make("Don't panic", kind="phrase")
    assert not state.solve("dont panic").correct
    assert state.solve("DON\u2019T PANIC").correct


def test_empty_solve_is_rejected_and_not_counted() -> None:
    state = make()
    with pytest.raises(InvalidGuessError):
        state.solve("   ")
    assert state.guesses == 0


def test_forfeit_after_max_guesses_is_scored_as_cap() -> None:
    state = make("buzzword")
    misses = [ch for ch in "ACEFGHIJKLMNPQSTVXY"]
    for letter in misses:
        state.guess_letter(letter)
    for i in range(MAX_GUESSES - len(misses)):
        state.solve(f"wrong answer {i}")
    assert state.guesses == MAX_GUESSES
    assert state.status is PuzzleStatus.FORFEITED
    assert state.score == MAX_GUESSES
    assert state.view()["answer"] == "BUZZWORD"


def test_correct_solve_on_last_guess_counts_as_solved() -> None:
    state = make("buzzword", max_guesses=3)
    state.guess_letter("q")
    state.guess_letter("x")
    state.solve("buzzword")
    assert state.status is PuzzleStatus.SOLVED
    assert state.score == 3


def test_custom_budget() -> None:
    state = make(max_guesses=2)
    state.guess_letter("q")
    state.guess_letter("x")
    assert state.status is PuzzleStatus.FORFEITED
    assert state.score == 2


def test_no_moves_after_finish() -> None:
    state = make("oxbow")
    state.solve("oxbow")
    with pytest.raises(PuzzleFinishedError):
        state.guess_letter("a")
    with pytest.raises(PuzzleFinishedError):
        state.solve("oxbow")
    with pytest.raises(PuzzleFinishedError):
        state.forfeit()


def test_explicit_forfeit() -> None:
    state = make()
    state.guess_letter("e")
    state.forfeit()
    assert state.status is PuzzleStatus.FORFEITED
    assert state.score == MAX_GUESSES


def test_puzzle_without_letters_is_invalid() -> None:
    with pytest.raises(ValueError):
        Puzzle("t-0002", "- -", "Nothing")


def test_view_hides_answer_until_finished() -> None:
    state = make("Don't panic", kind="phrase")
    view = state.view()
    assert view["answer"] is None
    assert view["mask"] == "___'_ _____"
    assert view["word_lengths"] == [4, 5]
    assert view["letters"] == 9
    state.solve("don't panic")
    assert state.view()["answer"] == "DON'T PANIC"
