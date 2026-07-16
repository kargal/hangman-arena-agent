"""Puzzle model and per-puzzle state machine.

A puzzle moves through three states::

    IN_PROGRESS --(all letters revealed / correct solve)--> SOLVED
    IN_PROGRESS --(guess budget exhausted / forfeit())-----> FORFEITED

Every letter guess and every solve attempt costs one guess. Repeated letters
and malformed input are rejected *before* anything is counted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from hangman_engine.errors import (
    InvalidGuessError,
    PuzzleFinishedError,
    RepeatedGuessError,
)
from hangman_engine.normalize import (
    hidden_letters,
    mask,
    normalize_answer,
    normalize_letter,
    word_lengths,
)

#: Guess budget per puzzle. A puzzle that is not solved within this many
#: guesses is forfeited and scored as ``MAX_GUESSES``.
MAX_GUESSES = 30


class PuzzleStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    SOLVED = "solved"
    FORFEITED = "forfeited"

    @property
    def finished(self) -> bool:
        return self is not PuzzleStatus.IN_PROGRESS


class GuessKind(str, Enum):
    LETTER = "letter"
    SOLVE = "solve"


@dataclass(frozen=True)
class Puzzle:
    """A single hangman puzzle as stored in a puzzle bank."""

    puzzle_id: str
    answer: str
    category: str
    kind: str = "word"  # "word" | "phrase"
    difficulty: str | None = None
    #: Calibrated reference difficulty: expected guesses for a fixed reference player.
    #: Used only for scoring (difficulty-adjusted learning slope); never shown to players.
    reference_guesses: float | None = None

    def __post_init__(self) -> None:
        if not hidden_letters(self.answer):
            raise ValueError(f"puzzle {self.puzzle_id!r} has no letters to guess")


@dataclass(frozen=True)
class GuessResult:
    """Outcome of one guess."""

    kind: GuessKind
    value: str
    correct: bool
    occurrences: int  # positions revealed by a letter guess (0 for solves)
    status: PuzzleStatus
    guesses: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "value": self.value,
            "correct": self.correct,
            "occurrences": self.occurrences,
            "status": self.status.value,
            "guesses": self.guesses,
        }


@dataclass
class PuzzleState:
    """Mutable play state for one puzzle."""

    puzzle: Puzzle
    max_guesses: int = MAX_GUESSES
    guessed_letters: list[str] = field(default_factory=list)
    solve_attempts: list[str] = field(default_factory=list)
    guesses: int = 0
    status: PuzzleStatus = PuzzleStatus.IN_PROGRESS

    # -- derived views ---------------------------------------------------

    @property
    def answer(self) -> str:
        return normalize_answer(self.puzzle.answer)

    @property
    def revealed(self) -> frozenset[str]:
        if self.status is PuzzleStatus.SOLVED:
            return hidden_letters(self.puzzle.answer)
        return frozenset(self.guessed_letters) & hidden_letters(self.puzzle.answer)

    @property
    def missed_letters(self) -> list[str]:
        targets = hidden_letters(self.puzzle.answer)
        return [ch for ch in self.guessed_letters if ch not in targets]

    @property
    def mask(self) -> str:
        return mask(self.puzzle.answer, self.revealed)

    @property
    def remaining(self) -> int:
        return max(0, self.max_guesses - self.guesses)

    @property
    def finished(self) -> bool:
        return self.status.finished

    @property
    def score(self) -> int | None:
        """Guesses charged for this puzzle, or ``None`` while in progress."""
        if self.status is PuzzleStatus.SOLVED:
            return self.guesses
        if self.status is PuzzleStatus.FORFEITED:
            return self.max_guesses
        return None

    # -- actions ---------------------------------------------------------

    def guess_letter(self, raw: str) -> GuessResult:
        """Guess a single letter. Costs one guess unless rejected."""
        self._require_in_progress()
        letter = normalize_letter(raw)
        if letter in self.guessed_letters:
            raise RepeatedGuessError(letter)

        self.guessed_letters.append(letter)
        self.guesses += 1
        occurrences = self.answer.count(letter)
        if hidden_letters(self.puzzle.answer) <= frozenset(self.guessed_letters):
            self.status = PuzzleStatus.SOLVED
        else:
            self._check_budget()
        return GuessResult(GuessKind.LETTER, letter, occurrences > 0, occurrences, self.status, self.guesses)

    def solve(self, attempt: str) -> GuessResult:
        """Attempt the full answer. Costs one guess; case/whitespace-insensitive."""
        self._require_in_progress()
        normalized = normalize_answer(attempt)
        if not normalized:
            raise InvalidGuessError("a solve attempt must not be empty")

        self.solve_attempts.append(normalized)
        self.guesses += 1
        correct = normalized == self.answer
        if correct:
            self.status = PuzzleStatus.SOLVED
        else:
            self._check_budget()
        return GuessResult(GuessKind.SOLVE, normalized, correct, 0, self.status, self.guesses)

    def forfeit(self) -> None:
        """Give up the puzzle. It is scored as ``max_guesses``."""
        self._require_in_progress()
        self.status = PuzzleStatus.FORFEITED

    # -- internals -------------------------------------------------------

    def _require_in_progress(self) -> None:
        if self.finished:
            raise PuzzleFinishedError(f"puzzle {self.puzzle.puzzle_id} is already {self.status.value}")

    def _check_budget(self) -> None:
        if self.guesses >= self.max_guesses:
            self.status = PuzzleStatus.FORFEITED

    # -- serialisation ---------------------------------------------------

    def view(self, *, reveal_answer: bool | None = None) -> dict[str, Any]:
        """Player-facing view. The answer is included only once finished."""
        show = self.finished if reveal_answer is None else reveal_answer
        return {
            "puzzle_id": self.puzzle.puzzle_id,
            "category": self.puzzle.category,
            "type": self.puzzle.kind,
            "mask": self.mask,
            "word_lengths": word_lengths(self.puzzle.answer),
            "letters": sum(word_lengths(self.puzzle.answer)),
            "status": self.status.value,
            "guesses": self.guesses,
            "max_guesses": self.max_guesses,
            "guessed_letters": list(self.guessed_letters),
            "missed_letters": self.missed_letters,
            "solve_attempts": list(self.solve_attempts),
            "answer": self.answer if show else None,
            "score": self.score,
        }
