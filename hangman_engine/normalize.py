"""Text normalisation and masking.

Only the 26 letters ``A``-``Z`` are ever hidden. Everything else in an answer --
spaces, hyphens, apostrophes, commas -- is shown to the player from the start.
All comparisons are case-insensitive.
"""

from __future__ import annotations

import string
import unicodedata

#: Character used for a hidden letter in a mask.
MASK_CHAR = "_"

HIDDEN_ALPHABET = frozenset(string.ascii_uppercase)

# Typographic punctuation that is folded to its ASCII equivalent.
_PUNCT_FOLD = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u02bc": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
    }
)


def normalize_answer(text: str) -> str:
    """Canonical form of an answer or solve attempt.

    Upper-cases, folds typographic quotes/dashes to ASCII, strips accents and
    collapses runs of whitespace to a single space.

    >>> normalize_answer("  rock   and roll ")
    'ROCK AND ROLL'
    >>> normalize_answer("Don\\u2019t panic")
    "DON'T PANIC"
    """
    text = unicodedata.normalize("NFKD", text.translate(_PUNCT_FOLD))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.upper().split())


def is_hidden(ch: str) -> bool:
    """True if ``ch`` is a letter that starts out hidden."""
    return ch.upper() in HIDDEN_ALPHABET and len(ch) == 1


def hidden_letters(answer: str) -> frozenset[str]:
    """Distinct hidden letters in ``answer`` (upper-case)."""
    return frozenset(ch for ch in normalize_answer(answer) if ch in HIDDEN_ALPHABET)


def normalize_letter(raw: str) -> str:
    """Validate and normalise a single-letter guess.

    Raises :class:`~hangman_engine.errors.InvalidGuessError` unless ``raw`` is
    exactly one ASCII letter (surrounding whitespace is ignored).
    """
    from hangman_engine.errors import InvalidGuessError

    letter = raw.strip().upper()
    if len(letter) != 1 or letter not in HIDDEN_ALPHABET:
        raise InvalidGuessError(f"a guess must be a single letter A-Z, got {raw!r}")
    return letter


def mask(answer: str, revealed: set[str] | frozenset[str]) -> str:
    """Mask ``answer``, showing only letters in ``revealed`` and non-letters.

    >>> mask("Jack-in-the-box", {"A", "E"})
    '_A__-__-__E-___'
    """
    out = []
    for ch in normalize_answer(answer):
        if ch in HIDDEN_ALPHABET and ch not in revealed:
            out.append(MASK_CHAR)
        else:
            out.append(ch)
    return "".join(out)


def word_lengths(answer: str) -> list[int]:
    """Number of hidden letters in each whitespace-separated word.

    >>> word_lengths("Don't panic")
    [4, 5]
    """
    return [sum(1 for ch in word if ch in HIDDEN_ALPHABET) for word in normalize_answer(answer).split(" ")]


def render_mask(masked: str) -> str:
    """Human-readable mask: one space between characters, three between words.

    >>> render_mask("_A__ __E")
    '_ A _ _   _ _ E'
    """
    return "   ".join(" ".join(word) for word in masked.split(" "))
