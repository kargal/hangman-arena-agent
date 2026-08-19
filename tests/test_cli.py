import json

import pytest

from arena_client import ArenaClient, cli
from tests.fake_arena import SESSION_ID, TOKEN, FakeArena


def run(arena: FakeArena, capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    client = ArenaClient("http://arena.test", TOKEN, SESSION_ID, transport=arena.transport)
    code = cli.main(list(argv), client=client)
    out, err = capsys.readouterr()
    return code, out, err


def test_next_prints_header_mask_and_counters(arena: FakeArena, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(arena, capsys, "next")
    assert code == 0
    assert out.splitlines() == [
        "Puzzle 1/3 [s9-0001] category: Landforms",
        "_ _ _ _ _ (5 letters)",
        "guesses: 0  misses: 0",
    ]


def test_guess_output(arena: FakeArena, capsys: pytest.CaptureFixture[str]) -> None:
    run(arena, capsys, "next")
    _, out, _ = run(arena, capsys, "guess", "o")
    assert out.splitlines() == [
        "'O' is in the answer (2 positions)",
        "O _ _ O _ (5 letters)",
        "guesses: 1  misses: 0",
    ]
    _, out, _ = run(arena, capsys, "guess", "Q")
    assert "'Q' is not in the answer" in out
    assert "guesses: 2  misses: 1 (Q)" in out


def test_solving_shows_answer_and_next_hint(arena: FakeArena, capsys: pytest.CaptureFixture[str]) -> None:
    run(arena, capsys, "next")
    _, out, _ = run(arena, capsys, "solve", "oxbow")
    assert "Correct!" in out
    assert "Solved! Answer: OXBOW - 1 guess" in out
    assert "Run `arena next` for puzzle 2/3." in out


def test_multi_word_solve_arguments_are_joined(arena: FakeArena, capsys: pytest.CaptureFixture[str]) -> None:
    run(arena, capsys, "next")
    run(arena, capsys, "solve", "oxbow")
    _, out, _ = run(arena, capsys, "next")
    assert "_ _ _ ' _   _ _ _ _ _ (2 words: 4, 5)" in out
    _, out, _ = run(arena, capsys, "solve", "don't", "PANIC")
    assert "Solved! Answer: DON'T PANIC" in out


def test_session_summary_after_last_puzzle(arena: FakeArena, capsys: pytest.CaptureFixture[str]) -> None:
    for answer in ("oxbow", "don't panic"):
        run(arena, capsys, "next")
        run(arena, capsys, "solve", answer)
    run(arena, capsys, "next")
    run(arena, capsys, "solve", "teacup")
    _, out, _ = run(arena, capsys, "solve", "teaspoon")
    assert "Session complete: 3/3 puzzles" in out
    assert "average guesses/puzzle: 1.33" in out
    assert "solved: 3  forfeited: 0" in out
    assert "learning-curve slope: +0.500 guesses/round" in out


def test_forfeit_output(capsys: pytest.CaptureFixture[str]) -> None:
    arena = FakeArena([("oxbow", "Landforms"), ("teaspoon", "Around the House")], max_guesses=3)
    run(arena, capsys, "next")
    run(arena, capsys, "guess", "a")
    _, out, _ = run(arena, capsys, "guess", "e")
    assert "1 guess left before this puzzle is forfeited" in out
    _, out, _ = run(arena, capsys, "guess", "i")
    assert "Out of guesses. Answer: OXBOW - scored as 3 guesses" in out


def test_errors_go_to_stderr_with_exit_code_1(arena: FakeArena, capsys: pytest.CaptureFixture[str]) -> None:
    run(arena, capsys, "next")
    code, out, err = run(arena, capsys, "next")
    assert code == 1
    assert out == ""
    assert err.startswith("error: finish the current puzzle")


def test_repeated_letter_message(arena: FakeArena, capsys: pytest.CaptureFixture[str]) -> None:
    run(arena, capsys, "next")
    run(arena, capsys, "guess", "x")
    code, _, err = run(arena, capsys, "guess", "x")
    assert code == 1
    assert "already guessed (not counted)" in err


def test_json_flag(arena: FakeArena, capsys: pytest.CaptureFixture[str]) -> None:
    _, out, _ = run(arena, capsys, "--json", "next")
    assert json.loads(out)["puzzle"]["mask"] == "_____"
    code, out, _ = run(arena, capsys, "--json", "next")
    assert code == 1
    assert json.loads(out)["error"]["code"] == "puzzle_in_progress"


def test_status_and_history(arena: FakeArena, capsys: pytest.CaptureFixture[str]) -> None:
    _, out, _ = run(arena, capsys, "status")
    assert "No puzzle started yet" in out
    _, out, _ = run(arena, capsys, "history")
    assert out.strip() == "No finished puzzles yet."
    run(arena, capsys, "next")
    run(arena, capsys, "guess", "z")
    run(arena, capsys, "solve", "oxbow")
    _, out, _ = run(arena, capsys, "status")
    assert "completed: 1/3  avg guesses: 2.00" in out
    assert "Run `arena next` for puzzle 2/3." in out
    _, out, _ = run(arena, capsys, "history")
    lines = out.splitlines()
    assert lines[0].split() == ["#", "puzzle", "category", "guesses", "result", "answer"]
    assert lines[1].split() == ["1", "s9-0001", "Landforms", "2", "solved", "OXBOW"]


def test_missing_configuration_exits_2(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("ARENA_TOKEN", raising=False)
    monkeypatch.delenv("ARENA_SESSION", raising=False)
    assert cli.main(["status"]) == 2
    assert "ARENA_TOKEN" in capsys.readouterr().err


def test_summary_shows_difficulty_adjusted_slope() -> None:
    from arena_client.formatting import format_summary

    summary = {
        "puzzles": 2,
        "average_guesses": 4.5,
        "solved": 2,
        "forfeited": 0,
        "learning_curve_slope": 3.0,
        "difficulty_adjusted_slope": -0.5,
    }
    out = format_summary(summary, 2)
    assert "learning-curve slope: +3.000 guesses/round" in out
    assert "difficulty-adjusted slope: -0.500 guesses/round" in out
