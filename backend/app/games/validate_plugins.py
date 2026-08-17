from __future__ import annotations

import sys

from backend.app.games.plugins import (
    GamePluginValidationError,
    validate_game_plugins,
)


def main() -> int:
    try:
        plugins = validate_game_plugins()
    except GamePluginValidationError as error:
        print(str(error), file=sys.stderr)
        return 1

    names = "、".join(
        plugin.registration.catalog.name for plugin in plugins
    ) or "无"
    print(f"社区游戏插件校验通过：{len(plugins)} 个已发布（{names}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
