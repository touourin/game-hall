from __future__ import annotations

import json
import logging

from backend.app.logging_config import (
    RequestContextFilter,
    bind_game_context,
    bind_request_context,
    build_rotating_file_handler,
    reset_game_context,
    reset_request_context,
)


def test_json_log_contains_request_context_and_exception(tmp_path) -> None:
    log_path = tmp_path / "error.log"
    handler = build_rotating_file_handler(
        log_path,
        level=logging.INFO,
        retention_days=7,
    )
    logger = logging.getLogger("test.game_hall.json")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    tokens = bind_request_context("req-123", "GET", "/api/test")

    try:
        try:
            raise RuntimeError("测试异常")
        except RuntimeError:
            logger.exception(
                "request failed",
                extra={"event": "http.failed", "status_code": 500},
            )
    finally:
        reset_request_context(tokens)
        handler.close()
        logger.handlers = []

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert payload["level"] == "ERROR"
    assert payload["request_id"] == "req-123"
    assert payload["event"] == "http.failed"
    assert payload["status_code"] == 500
    assert payload["error_type"] == "RuntimeError"
    assert "测试异常" in payload["exception"]


def test_request_context_filter_uses_safe_defaults() -> None:
    record = logging.LogRecord(
        "test", logging.INFO, __file__, 1, "message", (), None
    )

    assert RequestContextFilter().filter(record) is True
    assert record.request_id == "-"
    assert record.request_method == "-"
    assert record.request_path == "-"


def test_json_log_contains_game_and_room_context(tmp_path) -> None:
    log_path = tmp_path / "app.log"
    handler = build_rotating_file_handler(
        log_path,
        level=logging.INFO,
        retention_days=7,
    )
    logger = logging.getLogger("test.game_hall.context")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    tokens = bind_game_context(
        game_key="minesweeper",
        room_code="MINE",
        socket_event="arcade:action",
        player_id="player-1",
        account_id="account-1",
        action="reveal",
    )

    try:
        logger.warning("game action rejected")
    finally:
        reset_game_context(tokens)
        handler.close()
        logger.handlers = []

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert payload["game_key"] == "minesweeper"
    assert payload["room_code"] == "MINE"
    assert payload["socket_event"] == "arcade:action"
    assert payload["player_id"] == "player-1"
    assert payload["account_id"] == "account-1"
    assert payload["action"] == "reveal"
