import pytest

from hangman_engine import (
    InvalidGuessError,
    hidden_letters,
    is_hidden,
    mask,
    normalize_answer,
    normalize_letter,
    render_mask,
    word_lengths,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("teaspoon", "TEASPOON"),
        ("  Rock   and\troll  ", "ROCK AND ROLL"),
        ("don\u2019t panic", "DON'T PANIC"),
        ("well\u2013to\u2013do", "WELL-TO-DO"),
        ("caf\u00e9", "CAFE"),
    ],
)
def test_normalize_answer(raw: str, expected: str) -> None:
    assert normalize_answer(raw) == expected


def test_only_ascii_letters_are_hidden() -> None:
    assert is_hidden("a") and is_hidden("Z")
    for ch in " -'.,!7":
        assert not is_hidden(ch)


def test_hidden_letters_are_distinct_and_uppercase() -> None:
    assert hidden_letters("Don't panic") == frozenset("DONTPAIC")


def test_mask_shows_punctuation_and_spaces() -> None:
    assert mask("Don't panic", set()) == "___'_ _____"
    assert mask("well-to-do", set()) == "____-__-__"


def test_mask_reveals_guessed_letters_case_insensitively() -> None:
    assert mask("Rock and roll", {"O", "R"}) == "RO__ ___ RO__"


@pytest.mark.parametrize(("raw", "letter"), [("e", "E"), (" Q ", "Q"), ("z", "Z")])
def test_normalize_letter(raw: str, letter: str) -> None:
    assert normalize_letter(raw) == letter


@pytest.mark.parametrize("raw", ["", "ab", "7", "-", "\u00e9", "  "])
def test_normalize_letter_rejects_non_letters(raw: str) -> None:
    with pytest.raises(InvalidGuessError):
        normalize_letter(raw)


def test_word_lengths_count_hidden_letters_only() -> None:
    assert word_lengths("teaspoon") == [8]
    assert word_lengths("Don't panic") == [4, 5]
    assert word_lengths("well-to-do") == [8]


def test_render_mask() -> None:
    assert render_mask("___") == "_ _ _"
    assert render_mask("R___ ___ R___") == "R _ _ _   _ _ _   R _ _ _"
