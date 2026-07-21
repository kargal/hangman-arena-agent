"""HTTP client for the Hangman Arena API (see ``docs/protocol.md``)."""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx

from arena_client.config import ArenaConfig

API_PREFIX = "/v1"


class ArenaError(Exception):
    """An error response from the arena server, or a transport failure."""

    def __init__(self, message: str, *, code: str = "error", status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code

    def __str__(self) -> str:
        return self.message


class ArenaClient:
    """Thin, synchronous wrapper around the session endpoints.

    All methods return the decoded JSON body as a ``dict``. Server-side errors
    are raised as :class:`ArenaError` with the server's error ``code``.

    >>> client = ArenaClient.from_env()          # doctest: +SKIP
    >>> client.next_puzzle()["puzzle"]["mask"]   # doctest: +SKIP
    '______'
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        session_id: str,
        *,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.session_id = session_id
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}", "User-Agent": "arena-client/0.3"},
            timeout=timeout,
            transport=transport,
        )

    @classmethod
    def from_config(cls, config: ArenaConfig, **kwargs: Any) -> ArenaClient:
        return cls(config.url, config.token, config.session_id, timeout=config.timeout, **kwargs)

    @classmethod
    def from_env(cls, **kwargs: Any) -> ArenaClient:
        return cls.from_config(ArenaConfig.from_env(), **kwargs)

    # -- context management ---------------------------------------------

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> ArenaClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # -- endpoints --------------------------------------------------------

    def status(self) -> dict[str, Any]:
        """Session progress and the current puzzle (if any)."""
        return self._request("GET", "")

    def next_puzzle(self) -> dict[str, Any]:
        """Start the next puzzle. Fails while the current one is unfinished."""
        return self._request("POST", "/next")

    def guess(self, letter: str) -> dict[str, Any]:
        """Guess one letter in the current puzzle."""
        return self._request("POST", "/guess", json={"letter": letter})

    def solve(self, answer: str) -> dict[str, Any]:
        """Attempt to solve the current puzzle outright."""
        return self._request("POST", "/solve", json={"answer": answer})

    def history(self) -> dict[str, Any]:
        """All finished puzzles in this session, with answers and scores."""
        return self._request("GET", "/history")

    def summary(self) -> dict[str, Any]:
        """Aggregate session statistics."""
        return self._request("GET", "/summary")

    # -- internals ---------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{API_PREFIX}/sessions/{self.session_id}{path}"
        try:
            response = self._http.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise ArenaError(f"could not reach arena server: {exc}", code="connection_error") from exc

        try:
            body = response.json()
        except ValueError:
            body = None

        if response.is_error:
            error = body.get("error", {}) if isinstance(body, dict) else {}
            raise ArenaError(
                error.get("message") or f"HTTP {response.status_code}",
                code=error.get("code", "http_error"),
                status_code=response.status_code,
            )
        if not isinstance(body, dict):
            raise ArenaError("unexpected response from arena server", code="bad_response")
        return body
