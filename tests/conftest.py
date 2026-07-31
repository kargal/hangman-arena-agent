from __future__ import annotations

import pytest

from arena_client import ArenaClient
from tests.fake_arena import SESSION_ID, TOKEN, FakeArena

ANSWERS = [
    ("oxbow", "Landforms"),
    ("Don't panic", "Phrases"),
    ("teaspoon", "Around the House"),
]


@pytest.fixture
def arena() -> FakeArena:
    return FakeArena(ANSWERS)


@pytest.fixture
def client(arena: FakeArena) -> ArenaClient:
    return ArenaClient("http://arena.test", TOKEN, SESSION_ID, transport=arena.transport)
