from __future__ import annotations

import json
import logging
import os
import re
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any


DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_RETENTION_DAYS = 30
AVATAR_PATH_PATTERN = re.compile(r"(/api/avatars/)[A-Za-z0-9_-]+")
LOG_RECORD_FIELDS = {
    "account_id",
    "action",
    "avatar_preset",
    "client_ip",
    "duration_ms",
    "error_type",
    "event",
    "game_id",
    "game_key",
    "log_dir",
    "method",
    "mime_type",
    "path",
    "player_id",
    "reason",
    "room_code",
    "socket_event",
    "status_code",
    "stored_bytes",
    "upload_bytes",
}

request_id_context: ContextVar[str] = ContextVar(
    "request_id", default="-"
)
request_method_context: ContextVar[str] = ContextVar(
    "request_method", default="-"
)
request_path_context: ContextVar[str] = ContextVar(
    "request_path", default="-"
)
game_key_context: ContextVar[str | None] = ContextVar(
    "game_key", default=None
)
room_code_context: ContextVar[str | None] = ContextVar(
    "room_code", default=None
)
socket_event_context: ContextVar[str | None] = ContextVar(
    "socket_event", default=None
)
player_id_context: ContextVar[str | None] = ContextVar(
    "player_id", default=None
)
account_id_context: ContextVar[str | None] = ContextVar(
    "account_id", default=None
)
action_context: ContextVar[str | None] = ContextVar(
    "action", default=None
)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(
            record, "request_id", request_id_context.get()
        )
        record.request_method = getattr(
            record, "request_method", request_method_context.get()
        )
        record.request_path = getattr(
            record, "request_path", request_path_context.get()
        )
        contextual_fields = (
            ("game_key", game_key_context),
            ("room_code", room_code_context),
            ("socket_event", socket_event_context),
            ("player_id", player_id_context),
            ("account_id", account_id_context),
            ("action", action_context),
        )
        for field, context in contextual_fields:
            if getattr(record, field, None) is None:
                setattr(record, field, context.get())
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, timezone.utc
            ).astimezone().isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": AVATAR_PATH_PATTERN.sub(
                r"\1:token",
                record.getMessage(),
            ),
            "request_id": getattr(record, "request_id", "-"),
        }
        for field in LOG_RECORD_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
            if record.exc_info[0] is not None:
                payload.setdefault("error_type", record.exc_info[0].__name__)
        return json.dumps(payload, ensure_ascii=False, default=str)


def bind_request_context(
    request_id: str, method: str, path: str
) -> tuple[Token[str], Token[str], Token[str]]:
    return (
        request_id_context.set(request_id),
        request_method_context.set(method),
        request_path_context.set(path),
    )


def reset_request_context(
    tokens: tuple[Token[str], Token[str], Token[str]],
) -> None:
    request_id_context.reset(tokens[0])
    request_method_context.reset(tokens[1])
    request_path_context.reset(tokens[2])


GameContextTokens = tuple[
    Token[str | None],
    Token[str | None],
    Token[str | None],
    Token[str | None],
    Token[str | None],
    Token[str | None],
]


def bind_game_context(
    *,
    game_key: str | None,
    room_code: str | None,
    socket_event: str | None,
    player_id: str | None = None,
    account_id: str | None = None,
    action: str | None = None,
) -> GameContextTokens:
    return (
        game_key_context.set(game_key),
        room_code_context.set(room_code),
        socket_event_context.set(socket_event),
        player_id_context.set(player_id),
        account_id_context.set(account_id),
        action_context.set(action),
    )


def reset_game_context(tokens: GameContextTokens) -> None:
    game_key_context.reset(tokens[0])
    room_code_context.reset(tokens[1])
    socket_event_context.reset(tokens[2])
    player_id_context.reset(tokens[3])
    account_id_context.reset(tokens[4])
    action_context.reset(tokens[5])


def _positive_int(value: str | int | None, fallback: int) -> int:
    try:
        parsed = int(value) if value is not None else fallback
    except (TypeError, ValueError):
        return fallback
    return max(1, min(parsed, 365))


def _log_level(value: str | int | None) -> int:
    if isinstance(value, int):
        return value
    candidate = (value or DEFAULT_LOG_LEVEL).upper()
    resolved = logging.getLevelName(candidate)
    return resolved if isinstance(resolved, int) else logging.INFO


def build_rotating_file_handler(
    path: Path,
    *,
    level: int,
    retention_days: int,
) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(
        path,
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8",
        delay=True,
    )
    handler.setLevel(level)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestContextFilter())
    handler._game_hall_handler = True  # type: ignore[attr-defined]
    return handler


def configure_logging(
    *,
    log_dir: str | Path | None = None,
    level: str | int | None = None,
    retention_days: str | int | None = None,
) -> Path:
    resolved_dir = Path(
        log_dir or os.getenv("LOG_DIR") or Path.cwd() / ".data" / "logs"
    )
    resolved_dir.mkdir(parents=True, exist_ok=True)
    resolved_level = _log_level(level or os.getenv("LOG_LEVEL"))
    resolved_retention = _positive_int(
        retention_days or os.getenv("LOG_RETENTION_DAYS"),
        DEFAULT_RETENTION_DAYS,
    )

    root = logging.getLogger()
    root.setLevel(resolved_level)
    for handler in list(root.handlers):
        if getattr(handler, "_game_hall_handler", False):
            root.removeHandler(handler)
            handler.close()

    context_filter = RequestContextFilter()
    console = logging.StreamHandler()
    console.setLevel(resolved_level)
    console.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s "
            "[request_id=%(request_id)s] %(message)s"
        )
    )
    console.addFilter(context_filter)
    console._game_hall_handler = True  # type: ignore[attr-defined]

    application_file = build_rotating_file_handler(
        resolved_dir / "app.log",
        level=resolved_level,
        retention_days=resolved_retention,
    )
    error_file = build_rotating_file_handler(
        resolved_dir / "error.log",
        level=logging.ERROR,
        retention_days=resolved_retention,
    )
    root.addHandler(console)
    root.addHandler(application_file)
    root.addHandler(error_file)

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "socketio.server",
        "engineio.server",
        "game_hall.socketio",
        "game_hall.engineio",
    ):
        managed_logger = logging.getLogger(logger_name)
        managed_logger.handlers.clear()
        managed_logger.propagate = True
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("game_hall.socketio").setLevel(logging.WARNING)
    logging.getLogger("game_hall.engineio").setLevel(logging.WARNING)

    return resolved_dir
