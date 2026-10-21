"""Plain-text rendering of arena responses for the ``arena`` CLI."""

from __future__ import annotations

from typing import Any

from hangman_engine.normalize import render_mask

#: When this few guesses remain, the CLI prints a warning line.
LOW_BUDGET_WARNING = 5


def describe_lengths(word_lengths: list[int]) -> str:
    if len(word_lengths) == 1:
        n = word_lengths[0]
        return f"{n} letter{'s' if n != 1 else ''}"
    return f"{len(word_lengths)} words: " + ", ".join(str(n) for n in word_lengths)


def format_header(puzzle: dict[str, Any]) -> str:
    return f"Puzzle {puzzle['index']}/{puzzle['total']} [{puzzle['puzzle_id']}] category: {puzzle['category']}"


def format_board(puzzle: dict[str, Any]) -> str:
    """Mask line plus the guess/miss counter."""
    missed = puzzle.get("missed_letters", [])
    misses = f"{len(missed)}" + (f" ({', '.join(missed)})" if missed else "")
    lines = [
        f"{render_mask(puzzle['mask'])} ({describe_lengths(puzzle['word_lengths'])})",
        f"guesses: {puzzle['guesses']}  misses: {misses}",
    ]
    remaining = puzzle["max_guesses"] - puzzle["guesses"]
    if puzzle["status"] == "in_progress" and remaining <= LOW_BUDGET_WARNING:
        lines.append(f"{remaining} guess{'es' if remaining != 1 else ''} left before this puzzle is forfeited")
    return "\n".join(lines)


def format_puzzle(puzzle: dict[str, Any]) -> str:
    return f"{format_header(puzzle)}\n{format_board(puzzle)}"


def format_result(result: dict[str, Any]) -> str:
    value = result["value"]
    if result["kind"] == "letter":
        if result["correct"]:
            n = result["occurrences"]
            return f"'{value}' is in the answer ({n} position{'s' if n != 1 else ''})"
        return f"'{value}' is not in the answer"
    return "Correct!" if result["correct"] else f'"{value}" is not the answer'


def format_outcome(puzzle: dict[str, Any]) -> str:
    if puzzle["status"] == "solved":
        n = puzzle["score"]
        return f"Solved! Answer: {puzzle['answer']} - {n} guess{'es' if n != 1 else ''}"
    return f"Out of guesses. Answer: {puzzle['answer']} - scored as {puzzle['score']} guesses"


def format_summary(summary: dict[str, Any], total: int) -> str:
    slope = summary.get("learning_curve_slope")
    adjusted = summary.get("difficulty_adjusted_slope")
    lines = [
        f"Session complete: {summary['puzzles']}/{total} puzzles",
        f"average guesses/puzzle: {summary['average_guesses']:.2f}",
        f"solved: {summary['solved']}  forfeited: {summary['forfeited']}",
    ]
    if slope is not None:
        lines.append(f"learning-curve slope: {slope:+.3f} guesses/round")
    if adjusted is not None:
        lines.append(f"difficulty-adjusted slope: {adjusted:+.3f} guesses/round")
    return "\n".join(lines)


def format_next_hint(session: dict[str, Any]) -> str:
    return f"Run `arena next` for puzzle {session['completed'] + 1}/{session['total']}."


def _entry_name(entry: dict[str, Any]) -> str:
    if entry.get("you"):
        return f"you ({entry['model']})" if entry.get("model") else "you"
    return str(entry.get("label") or entry.get("model") or "unknown")


def format_standings(standings: dict[str, Any], total: int | None = None) -> str:
    """Compact table of the season's live standings; this session is marked with ``>``."""
    entries = standings.get("entries", [])
    if not entries:
        return f"Season {standings.get('season', '?')} standings: no finished puzzles yet."
    lines = [f"Season {standings.get('season', '?')} standings (live, avg guesses/puzzle, lower is better):"]
    names = [_entry_name(e) for e in entries]
    rank_w = max(len(str(e["rank"])) for e in entries)
    name_w = max(len(n) for n in names)
    for entry, name in zip(entries, names, strict=True):
        done = f"{entry['completed']}/{total}" if total else str(entry["completed"])
        avg = entry.get("average_guesses")
        avg_txt = f"{avg:.2f}" if avg is not None else "-"
        mark = ">" if entry.get("you") else " "
        lines.append(f"{mark} {str(entry['rank']).rjust(rank_w)}. {name.ljust(name_w)}  {done.rjust(5)}  {avg_txt}")
    return "\n".join(lines)


def format_after_move(body: dict[str, Any]) -> str:
    """Full output after ``arena guess`` / ``arena solve``."""
    puzzle, session = body["puzzle"], body["session"]
    parts = [format_result(body["result"]), format_board(puzzle)]
    if puzzle["status"] != "in_progress":
        parts.append(format_outcome(puzzle))
        if session["finished"] and body.get("summary"):
            parts.append(format_summary(body["summary"], session["total"]))
        if body.get("standings"):
            parts.append(format_standings(body["standings"], session["total"]))
        if not session["finished"]:
            parts.append(format_next_hint(session))
    return "\n".join(parts)


def format_standings_response(body: dict[str, Any]) -> str:
    """Output of ``arena standings``."""
    session = body["session"]
    return f"{format_session_line(session)}\n{format_standings(body['standings'], session['total'])}"


def format_session_line(session: dict[str, Any]) -> str:
    avg = session.get("average_guesses")
    avg_txt = f"  avg guesses: {avg:.2f}" if avg is not None else ""
    return (
        f"Session {session['session_id']} (season {session['season']})"
        f"  completed: {session['completed']}/{session['total']}{avg_txt}"
    )


def format_status(body: dict[str, Any]) -> str:
    session, puzzle = body["session"], body.get("puzzle")
    parts = [format_session_line(session)]
    if puzzle is None:
        parts.append("No puzzle started yet. Run `arena next` to begin.")
    else:
        parts.append(format_puzzle(puzzle))
        if puzzle["status"] != "in_progress":
            parts.append(format_outcome(puzzle))
            parts.append("Session complete." if session["finished"] else format_next_hint(session))
    return "\n".join(parts)


def format_history(body: dict[str, Any]) -> str:
    puzzles = body.get("puzzles", [])
    if not puzzles:
        return "No finished puzzles yet."
    rows = [("#", "puzzle", "category", "guesses", "result", "answer")]
    for p in puzzles:
        rows.append((str(p["index"]), p["puzzle_id"], p["category"], str(p["score"]), p["status"], p["answer"] or ""))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]) - 1)]
    lines = []
    for r in rows:
        cells = [
            r[0].rjust(widths[0]),
            r[1].ljust(widths[1]),
            r[2].ljust(widths[2]),
            r[3].rjust(widths[3]),
            r[4].ljust(widths[4]),
            r[5],
        ]
        lines.append("  ".join(cells).rstrip())
    return "\n".join(lines)
