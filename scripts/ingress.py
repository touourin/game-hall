from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import ssl
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
BASE_COMPOSE_FILE = PROJECT_DIR / "compose.yaml"
HTTP_COMPOSE_FILE = PROJECT_DIR / "compose.override.yaml"
HTTPS_COMPOSE_FILE = PROJECT_DIR / "compose.https.yaml"
CADDYFILE_PATH = PROJECT_DIR / "Caddyfile"
ENV_FILE_PATH = PROJECT_DIR / ".env"

APPLICATION_SERVICE = "app"
HTTPS_SERVICE = "caddy"
APPLICATION_CONTAINER = "game-hall-app"
HTTPS_CONTAINER = "game-hall-caddy"
DEFAULT_HTTP_PORT = 10618
DEFAULT_HTTPS_BACKEND_PORT = 10618

HOSTNAME_LABEL_PATTERN = re.compile(
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
)


@dataclass(frozen=True)
class IngressConfig:
    https_enabled: bool
    app_host_port: int = DEFAULT_HTTP_PORT
    bind_host: str = "0.0.0.0"
    domain: str | None = None

    @property
    def compose_files(self) -> tuple[Path, Path]:
        ingress_file = HTTPS_COMPOSE_FILE if self.https_enabled else HTTP_COMPOSE_FILE
        return BASE_COMPOSE_FILE, ingress_file

    @property
    def services(self) -> tuple[str, ...]:
        if self.https_enabled:
            return APPLICATION_SERVICE, HTTPS_SERVICE
        return (APPLICATION_SERVICE,)


HTTP_INGRESS = IngressConfig(https_enabled=False)
HTTPS_COMPOSE_LAYOUT = IngressConfig(
    https_enabled=True,
    app_host_port=DEFAULT_HTTPS_BACKEND_PORT,
    bind_host="127.0.0.1",
    domain="localhost",
)


def read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        key, separator, raw_value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            raise RuntimeError(f"Invalid .env entry on line {line_number}")

        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def environment_setting(
    name: str,
    dotenv: Mapping[str, str],
    *,
    default: str = "",
) -> str:
    return os.environ.get(name, dotenv.get(name, default)).strip()


def parse_port(
    raw_value: str,
    *,
    name: str,
    reserved: set[int] | None = None,
) -> int:
    try:
        port = int(raw_value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be an integer") from error
    if not 1 <= port <= 65535 or port in (reserved or set()):
        suffix = " and cannot be 80 or 443" if reserved else ""
        raise RuntimeError(f"{name} must be between 1 and 65535{suffix}")
    return port


def normalize_public_domain(raw_domain: str) -> str:
    if not raw_domain:
        raise RuntimeError("HTTPS_DOMAIN is required when HTTPS_ENABLED=1")
    if any(character in raw_domain for character in "/:*"):
        raise RuntimeError(
            "HTTPS_DOMAIN must be a hostname without a scheme, port, or wildcard"
        )

    try:
        domain = raw_domain.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise RuntimeError("HTTPS_DOMAIN is not a valid hostname") from error

    if len(domain) > 253 or "." not in domain:
        raise RuntimeError("HTTPS_DOMAIN must be a publicly resolvable domain name")
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise RuntimeError("HTTPS_DOMAIN must be a domain name, not an IP address")

    labels = domain.split(".")
    if any(HOSTNAME_LABEL_PATTERN.fullmatch(label) is None for label in labels):
        raise RuntimeError("HTTPS_DOMAIN is not a valid hostname")
    return domain


def load_ingress_config(path: Path = ENV_FILE_PATH) -> IngressConfig:
    dotenv = read_dotenv(path)
    enabled_value = environment_setting(
        "HTTPS_ENABLED",
        dotenv,
        default="0",
    )
    if enabled_value not in {"0", "1"}:
        raise RuntimeError("HTTPS_ENABLED must be 0 or 1")

    http_port = parse_port(
        environment_setting(
            "GAME_HALL_PORT",
            dotenv,
            default=environment_setting(
                "AVALON_PORT",
                dotenv,
                default=str(DEFAULT_HTTP_PORT),
            ),
        ),
        name="GAME_HALL_PORT",
    )
    if enabled_value == "0":
        return IngressConfig(
            https_enabled=False,
            app_host_port=http_port,
            bind_host=environment_setting(
                "GAME_HALL_BIND_HOST",
                dotenv,
                default="0.0.0.0",
            ),
        )

    return IngressConfig(
        https_enabled=True,
        app_host_port=parse_port(
            environment_setting(
                "HTTPS_BACKEND_PORT",
                dotenv,
                default=str(DEFAULT_HTTPS_BACKEND_PORT),
            ),
            name="HTTPS_BACKEND_PORT",
            reserved={80, 443},
        ),
        bind_host="127.0.0.1",
        domain=normalize_public_domain(
            environment_setting("HTTPS_DOMAIN", dotenv),
        ),
    )


def compose_command(ingress: IngressConfig, *arguments: str) -> list[str]:
    command = ["docker", "compose"]
    for compose_file in ingress.compose_files:
        command.extend(["--file", str(compose_file)])
    command.extend(arguments)
    return command


def compose_environment(ingress: IngressConfig) -> Mapping[str, str]:
    environment = os.environ.copy()
    if ingress.https_enabled:
        environment.update(
            {
                "HTTPS_BACKEND_PORT": str(ingress.app_host_port),
                "HTTPS_DOMAIN": ingress.domain or "",
            }
        )
    else:
        environment.update(
            {
                "GAME_HALL_BIND_HOST": ingress.bind_host,
                "GAME_HALL_PORT": str(ingress.app_host_port),
            }
        )
    return environment


def container_is_running(inspection: dict[str, object] | None) -> bool:
    if inspection is None:
        return False
    state = inspection.get("State")
    return isinstance(state, dict) and state.get("Running") is True


def parse_container_inspection(payload: str) -> dict[str, object] | None:
    try:
        inspections = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(inspections, list) or not inspections:
        return None
    inspection = inspections[0]
    return inspection if isinstance(inspection, dict) else None


def container_environment(inspection: dict[str, object] | None) -> dict[str, str]:
    if inspection is None:
        return {}
    config = inspection.get("Config")
    if not isinstance(config, dict):
        return {}
    entries = config.get("Env")
    if not isinstance(entries, list):
        return {}

    environment: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, str):
            continue
        name, separator, value = entry.partition("=")
        if separator:
            environment[name] = value
    return environment


def published_app_binding(
    inspection: dict[str, object] | None,
) -> tuple[str, int] | None:
    if inspection is None:
        return None
    network = inspection.get("NetworkSettings")
    if not isinstance(network, dict):
        return None
    ports = network.get("Ports")
    if not isinstance(ports, dict):
        return None
    bindings = ports.get("8000/tcp")
    if not isinstance(bindings, list):
        return None

    candidates = [binding for binding in bindings if isinstance(binding, dict)]
    for binding in candidates:
        host = binding.get("HostIp")
        port = binding.get("HostPort")
        if isinstance(host, str) and host != "::" and isinstance(port, str):
            try:
                return host or "0.0.0.0", int(port)
            except ValueError:
                continue
    return None


def https_responds(ingress: IngressConfig, timeout: float = 3) -> bool:
    if not ingress.https_enabled or ingress.domain is None:
        return True

    request = (
        f"GET / HTTP/1.1\r\nHost: {ingress.domain}\r\n"
        "Connection: close\r\n\r\n"
    ).encode("ascii")
    try:
        context = ssl.create_default_context()
        with socket.create_connection(("127.0.0.1", 443), timeout=timeout) as raw:
            with context.wrap_socket(raw, server_hostname=ingress.domain) as secure:
                secure.settimeout(timeout)
                secure.sendall(request)
                with secure.makefile("rb") as response:
                    status_line = response.readline(4096).decode(
                        "ascii",
                        errors="replace",
                    )
        status_code = int(status_line.split(" ", 2)[1])
    except (IndexError, OSError, ssl.SSLError, ValueError):
        return False
    return 200 <= status_code < 400
