"""Exceptions raised by the game engine."""

from __future__ import annotations


class HangmanError(Exception):
    """Base class for all engine errors.

    ``code`` is a stable, machine-readable identifier that the arena server
    forwards to clients unchanged (see ``docs/protocol.md``).
    """

    code = "hangman_error"


class InvalidGuessError(HangmanError, ValueError):
    """The guess is malformed (not a single A-Z letter, empty solve, ...)."""

    code = "invalid_guess"


class RepeatedGuessError(HangmanError):
    """The letter was already guessed for this puzzle. Not counted."""

    code = "repeated_guess"

    def __init__(self, letter: str) -> None:
        super().__init__(f"letter {letter!r} was already guessed (not counted)")
        self.letter = letter


class PuzzleFinishedError(HangmanError):
    """The puzzle is already solved or forfeited."""

    code = "puzzle_finished"
