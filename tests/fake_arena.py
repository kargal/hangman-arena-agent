"""In-process fake of the arena server, implemented on ``httpx.MockTransport``.

It follows ``docs/protocol.md`` closely enough to exercise the client and CLI
without a network. Puzzles are judged with the real ``hangman_engine``.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from hangman_engine import HangmanError, Puzzle, PuzzleState, summarize

SESSION_ID = "ses_test0000000001"
TOKEN = "tok-test"

_ROUTE = re.compile(r"^/v1/sessions/(?P<sid>[^/]+)(?P<action>/[a-z]+)?$")


class FakeArena:
    """``others`` are standings entries of other sessions: dicts with ``label``, ``model``, ``agent``,
    ``completed`` and ``average_guesses``; they are ranked together with this session."""

    def __init__(
        self,
        answers: list[tuple[str, str]],
        *,
        max_guesses: int = 30,
        others: list[dict[str, Any]] | None = None,
    ) -> None:
        self.puzzles = [
            Puzzle(f"s9-{i:04d}", answer, category, "phrase" if " " in answer else "word")
            for i, (answer, category) in enumerate(answers, start=1)
        ]
        self.max_guesses = max_guesses
        self.others = list(others or [])
        self.states: list[PuzzleState] = []
        self.requests: list[httpx.Request] = []

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handle)

    # -- views -----------------------------------------------------------

    def _session(self) -> dict[str, Any]:
        stats = summarize(self.states)
        return {
            "session_id": SESSION_ID,
            "season": 9,
            "total": len(self.puzzles),
            "completed": stats.puzzles,
            "current_index": len(self.states),
            "finished": stats.puzzles == len(self.puzzles),
            "average_guesses": stats.average_guesses,
            "agent": "test",
            "model": "test-model",
            "created_at": "2026-01-01T00:00:00Z",
        }

    def _puzzle(self, index: int) -> dict[str, Any]:
        return {"index": index, "total": len(self.puzzles), **self.states[index - 1].view()}

    def _standings(self) -> dict[str, Any]:
        session = self._session()
        rows = [dict(o, you=False) for o in self.others if o["completed"] > 0]
        if session["completed"] > 0:
            rows.append(
                {
                    "label": "test-model (test)",
                    "model": session["model"],
                    "agent": session["agent"],
                    "completed": session["completed"],
                    "average_guesses": session["average_guesses"],
                    "you": True,
                }
            )
        rows.sort(key=lambda r: (r["average_guesses"], -r["completed"]))
        entries, previous = [], None
        for position, row in enumerate(rows, start=1):
            key = (round(row["average_guesses"], 3), row["completed"])
            rank = entries[-1]["rank"] if key == previous else position
            entries.append({"rank": rank, **row})
            previous = key
        return {"season": 9, "as_of": "2026-01-01T00:00:00Z", "entries": entries}

    @staticmethod
    def _error(status: int, code: str, message: str) -> httpx.Response:
        return httpx.Response(status, json={"error": {"code": code, "message": message}})

    # -- routing ---------------------------------------------------------

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        match = _ROUTE.match(request.url.path)
        if not match:
            return self._error(404, "not_found", "no such endpoint")
        if match["sid"] != SESSION_ID:
            return self._error(404, "session_not_found", f"unknown session {match['sid']}")
        if request.headers.get("Authorization") != f"Bearer {TOKEN}":
            return self._error(401, "unauthorized", "invalid token for this session")

        action = match["action"] or ""
        current = self.states[-1] if self.states else None

        if request.method == "GET" and action == "":
            return httpx.Response(
                200, json={"session": self._session(), "puzzle": self._puzzle(len(self.states)) if current else None}
            )
        if request.method == "GET" and action == "/history":
            done = [self._puzzle(i) for i, s in enumerate(self.states, 1) if s.finished]
            return httpx.Response(200, json={"session": self._session(), "puzzles": done})
        if request.method == "GET" and action == "/summary":
            stats = summarize(self.states)
            scores = [s.score for s in self.states if s.finished]
            return httpx.Response(200, json={"session": self._session(), "scores": scores, "summary": stats.to_dict()})
        if request.method == "GET" and action == "/standings":
            return httpx.Response(200, json={"session": self._session(), "standings": self._standings()})
        if request.method == "POST" and action == "/next":
            if current is not None and not current.finished:
                return self._error(409, "puzzle_in_progress", "finish the current puzzle before requesting the next")
            if len(self.states) == len(self.puzzles):
                return self._error(409, "session_complete", "all puzzles in this session are finished")
            self.states.append(PuzzleState(self.puzzles[len(self.states)], max_guesses=self.max_guesses))
            return httpx.Response(200, json={"session": self._session(), "puzzle": self._puzzle(len(self.states))})
        if request.method == "POST" and action in ("/guess", "/solve"):
            if current is None or current.finished:
                return self._error(409, "no_active_puzzle", "no puzzle in progress; run `arena next`")
            payload = json.loads(request.content or b"{}")
            try:
                result = (
                    current.guess_letter(payload["letter"]) if action == "/guess" else current.solve(payload["answer"])
                )
            except HangmanError as exc:
                status = 400 if exc.code == "invalid_guess" else 409
                return self._error(status, exc.code, str(exc))
            body: dict[str, Any] = {
                "session": self._session(),
                "puzzle": self._puzzle(len(self.states)),
                "result": result.to_dict(),
            }
            if body["session"]["finished"]:
                body["summary"] = summarize(self.states).to_dict()
            if current.finished:
                body["standings"] = self._standings()
            return httpx.Response(200, json=body)
        return self._error(405, "method_not_allowed", "method not allowed")
