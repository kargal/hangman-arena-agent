"""Client configuration, read from the environment."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_URL = "http://arena:8080"


class ConfigError(RuntimeError):
    """Required configuration is missing or invalid."""


@dataclass(frozen=True)
class ArenaConfig:
    """Connection settings for one arena session.

    ========================  =========================================
    ``ARENA_URL``             server base URL (default ``http://arena:8080``)
    ``ARENA_TOKEN``           bearer token issued for the session
    ``ARENA_SESSION``         session id, e.g. ``ses_4f1c2a9b0e7d3c11``
    ``ARENA_TIMEOUT``         request timeout in seconds (default 30)
    ========================  =========================================
    """

    url: str
    token: str
    session_id: str
    timeout: float = 30.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> ArenaConfig:
        env = os.environ if env is None else env
        missing = [name for name in ("ARENA_TOKEN", "ARENA_SESSION") if not env.get(name)]
        if missing:
            raise ConfigError(
                "missing environment variable(s): " + ", ".join(missing) + " (these are set by the arena runner)"
            )
        try:
            timeout = float(env.get("ARENA_TIMEOUT", "30"))
        except ValueError as exc:
            raise ConfigError(f"ARENA_TIMEOUT must be a number, got {env['ARENA_TIMEOUT']!r}") from exc
        return cls(
            url=(env.get("ARENA_URL") or DEFAULT_URL).rstrip("/"),
            token=env["ARENA_TOKEN"],
            session_id=env["ARENA_SESSION"],
            timeout=timeout,
        )
