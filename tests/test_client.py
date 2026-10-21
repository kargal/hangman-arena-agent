import httpx
import pytest

from arena_client import ArenaClient, ArenaConfig, ArenaError, ConfigError
from tests.fake_arena import SESSION_ID, FakeArena


def test_sends_bearer_token_and_session_path(client: ArenaClient, arena: FakeArena) -> None:
    client.status()
    request = arena.requests[-1]
    assert request.headers["Authorization"].startswith("Bearer ")
    assert request.url.path == f"/v1/sessions/{SESSION_ID}"


def test_status_before_first_puzzle(client: ArenaClient) -> None:
    body = client.status()
    assert body["puzzle"] is None
    assert body["session"]["completed"] == 0


def test_next_returns_masked_puzzle_without_answer(client: ArenaClient) -> None:
    puzzle = client.next_puzzle()["puzzle"]
    assert puzzle["index"] == 1
    assert puzzle["mask"] == "_____"
    assert puzzle["answer"] is None


def test_guess_and_solve_round_trip(client: ArenaClient) -> None:
    client.next_puzzle()
    body = client.guess("o")
    assert body["result"] == {
        "kind": "letter",
        "value": "O",
        "correct": True,
        "occurrences": 2,
        "status": "in_progress",
        "guesses": 1,
    }
    body = client.solve("OXBOW")
    assert body["puzzle"]["status"] == "solved"
    assert body["puzzle"]["score"] == 2


def test_next_while_puzzle_in_progress_is_rejected(client: ArenaClient) -> None:
    client.next_puzzle()
    with pytest.raises(ArenaError) as info:
        client.next_puzzle()
    assert info.value.code == "puzzle_in_progress"
    assert info.value.status_code == 409


def test_repeated_guess_error_code(client: ArenaClient) -> None:
    client.next_puzzle()
    client.guess("x")
    with pytest.raises(ArenaError) as info:
        client.guess("x")
    assert info.value.code == "repeated_guess"
    assert client.status()["puzzle"]["guesses"] == 1


def test_history_and_summary(client: ArenaClient) -> None:
    client.next_puzzle()
    client.solve("oxbow")
    history = client.history()["puzzles"]
    assert [p["answer"] for p in history] == ["OXBOW"]
    summary = client.summary()
    assert summary["scores"] == [1]
    assert summary["summary"]["solved"] == 1


def test_bad_token_raises_unauthorized(arena: FakeArena) -> None:
    client = ArenaClient("http://arena.test", "wrong", SESSION_ID, transport=arena.transport)
    with pytest.raises(ArenaError) as info:
        client.status()
    assert info.value.code == "unauthorized"


def test_transport_errors_are_wrapped() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = ArenaClient("http://arena.test", "t", "s", transport=httpx.MockTransport(boom))
    with pytest.raises(ArenaError) as info:
        client.status()
    assert info.value.code == "connection_error"


def test_non_json_error_body() -> None:
    client = ArenaClient(
        "http://arena.test", "t", "s", transport=httpx.MockTransport(lambda r: httpx.Response(502, text="bad gateway"))
    )
    with pytest.raises(ArenaError) as info:
        client.status()
    assert info.value.status_code == 502
    assert info.value.code == "http_error"


def test_config_from_env_defaults() -> None:
    config = ArenaConfig.from_env({"ARENA_TOKEN": "t", "ARENA_SESSION": "s"})
    assert config.url == "http://arena:8080"
    assert config.timeout == 30.0


def test_config_strips_trailing_slash() -> None:
    config = ArenaConfig.from_env({"ARENA_URL": "http://localhost:8080/", "ARENA_TOKEN": "t", "ARENA_SESSION": "s"})
    assert config.url == "http://localhost:8080"


def test_config_requires_token_and_session() -> None:
    with pytest.raises(ConfigError, match="ARENA_TOKEN, ARENA_SESSION"):
        ArenaConfig.from_env({})


def test_config_rejects_bad_timeout() -> None:
    with pytest.raises(ConfigError):
        ArenaConfig.from_env({"ARENA_TOKEN": "t", "ARENA_SESSION": "s", "ARENA_TIMEOUT": "soon"})


def test_standings_endpoint(client: ArenaClient, arena: FakeArena) -> None:
    body = client.standings()
    assert body["standings"]["entries"] == []
    assert arena.requests[-1].url.path == f"/v1/sessions/{SESSION_ID}/standings"
    client.next_puzzle()
    body = client.solve("oxbow")
    assert body["standings"]["entries"][0]["you"] is True
    assert body["standings"]["entries"][0]["completed"] == 1
