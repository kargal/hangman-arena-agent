"""``arena`` -- command-line client for Hangman Arena.

    arena next              start the next puzzle
    arena guess <letter>    guess one letter
    arena solve "<answer>"  attempt the whole answer
    arena status            show the current puzzle and session progress
    arena history           list finished puzzles with answers and guess counts

Connection settings come from ``ARENA_URL``, ``ARENA_TOKEN`` and
``ARENA_SESSION`` (set by the arena runner). Add ``--json`` to any command to
print the raw server response instead of formatted text.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from typing import Any

from arena_client import formatting
from arena_client.client import ArenaClient, ArenaError
from arena_client.config import ArenaConfig, ConfigError

EXIT_OK = 0
EXIT_ARENA_ERROR = 1
EXIT_USAGE = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arena",
        description="Play Hangman Arena puzzles from the command line.",
        epilog="Configuration: ARENA_URL, ARENA_TOKEN, ARENA_SESSION (see README.md).",
    )
    parser.add_argument("--json", action="store_true", help="print raw JSON responses")
    parser.add_argument("--version", action="version", version="%(prog)s 0.2.0")
    sub = parser.add_subparsers(dest="command", metavar="<command>", required=True)

    sub.add_parser("next", help="start the next puzzle (current one must be finished)")
    p_guess = sub.add_parser("guess", help="guess a single letter")
    p_guess.add_argument("letter", help="one letter A-Z (case-insensitive)")
    p_solve = sub.add_parser("solve", help="attempt the full answer (costs one guess)")
    p_solve.add_argument("answer", nargs="+", help='the full answer, e.g. "rock and roll"')
    sub.add_parser("status", help="show the current puzzle and session progress")
    sub.add_parser("history", help="list finished puzzles in this session")
    return parser


def _render_next(body: dict[str, Any]) -> str:
    return formatting.format_puzzle(body["puzzle"])


_COMMANDS: dict[
    str, tuple[Callable[[ArenaClient, argparse.Namespace], dict[str, Any]], Callable[[dict[str, Any]], str]]
] = {
    "next": (lambda c, a: c.next_puzzle(), _render_next),
    "guess": (lambda c, a: c.guess(a.letter), formatting.format_after_move),
    "solve": (lambda c, a: c.solve(" ".join(a.answer)), formatting.format_after_move),
    "status": (lambda c, a: c.status(), formatting.format_status),
    "history": (lambda c, a: c.history(), formatting.format_history),
}


def main(argv: Sequence[str] | None = None, *, client: ArenaClient | None = None) -> int:
    args = _build_parser().parse_args(argv)
    call, render = _COMMANDS[args.command]

    if client is None:
        try:
            client = ArenaClient.from_config(ArenaConfig.from_env())
        except ConfigError as exc:
            print(f"arena: {exc}", file=sys.stderr)
            return EXIT_USAGE

    try:
        body = call(client, args)
    except ArenaError as exc:
        if args.json:
            print(json.dumps({"error": {"code": exc.code, "message": exc.message}}))
        else:
            print(f"error: {exc.message}", file=sys.stderr)
        return EXIT_ARENA_ERROR
    finally:
        client.close()

    print(json.dumps(body, indent=2) if args.json else render(body))
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
