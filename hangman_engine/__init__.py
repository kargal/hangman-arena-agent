"""Game rules for Hangman Arena.

This package is the single source of truth for how puzzles are masked, how
guesses are judged and how sessions are scored. The arena server imports it
directly, so behaviour here is exactly what agents are evaluated against.
"""

from hangman_engine.errors import (
    HangmanError,
    InvalidGuessError,
    PuzzleFinishedError,
    RepeatedGuessError,
)
from hangman_engine.normalize import (
    MASK_CHAR,
    hidden_letters,
    is_hidden,
    mask,
    normalize_answer,
    normalize_letter,
    render_mask,
    word_lengths,
)
from hangman_engine.puzzle import (
    MAX_GUESSES,
    GuessKind,
    GuessResult,
    Puzzle,
    PuzzleState,
    PuzzleStatus,
)
from hangman_engine.scoring import (
    SessionStats,
    difficulty_adjusted_slope,
    excess_guesses,
    learning_curve,
    learning_curve_slope,
    puzzle_score,
    summarize,
)

__version__ = "0.3.1"

__all__ = [
    "MASK_CHAR",
    "MAX_GUESSES",
    "GuessKind",
    "GuessResult",
    "HangmanError",
    "InvalidGuessError",
    "Puzzle",
    "PuzzleFinishedError",
    "PuzzleState",
    "PuzzleStatus",
    "RepeatedGuessError",
    "SessionStats",
    "__version__",
    "difficulty_adjusted_slope",
    "excess_guesses",
    "hidden_letters",
    "is_hidden",
    "learning_curve",
    "learning_curve_slope",
    "mask",
    "normalize_answer",
    "normalize_letter",
    "puzzle_score",
    "render_mask",
    "summarize",
    "word_lengths",
]
