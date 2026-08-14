from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from backend.app.arcade.bots import ArcadeBotService, BotAction
from backend.app.arcade.models import (
    ArcadeChatMessage,
    ArcadePlayer,
    ArcadeRoom,
    utc_now_iso,
)
from backend.app.games.base import GameRuleError

from .bots import choose_ai_action
from .engine import GameEngine as AvalonRulesEngine
from .engine import GameRuleError as AvalonRuleError
from .models import (
    Alignment,
    AvalonMode,
    ChatMessage,
    GameSettings,
    Phase,
    Player,
    Room,
)
from .records import persist_avalon_match
from .views import build_player_view


class AvalonEngine:
    """Run Avalon inside the shared Arcade room lifecycle and protocol."""

    key = "avalon"
    name = "阿瓦隆"
    min_players = 5
    max_players = 10
    public_rooms = True
    uses_first_player = False
    manages_seating = True
    action_phases = {phase.value for phase in Phase if phase != Phase.GAME_OVER}

    def __init__(self, rules: AvalonRulesEngine | None = None) -> None:
        self.rules = rules or AvalonRulesEngine()

    def initial_state(self) -> None:
        return None

    @staticmethod
    def room_options(options: dict[str, Any]) -> dict[str, Any]:
        mode = options.get("mode", AvalonMode.STANDARD.value)
        if mode not in {item.value for item in AvalonMode}:
            raise GameRuleError("请选择有效的阿瓦隆玩法")

        lady_enabled = options.get("ladyEnabled", True)
        listed = options.get("listed", True)
        early_assassination = options.get("earlyAssassinationEnabled", False)
        shadow_merlin_enabled = options.get("shadowMerlinEnabled", False)
        if not all(
            isinstance(value, bool)
            for value in (
                lady_enabled,
                listed,
                early_assassination,
                shadow_merlin_enabled,
            )
        ):
            raise GameRuleError("阿瓦隆房间规则格式不正确")
        if mode == AvalonMode.COURT_UNDERCURRENT.value:
            lady_enabled = False
            early_assassination = False
        else:
            shadow_merlin_enabled = False
        return {
            "mode": mode,
            "shadowMerlinEnabled": shadow_merlin_enabled,
            "ladyEnabled": lady_enabled,
            "listed": listed,
            "earlyAssassinationEnabled": early_assassination,
        }

    @staticmethod
    def is_active_phase(phase: str) -> bool:
        return phase not in {Phase.LOBBY.value, "finished"}

    @staticmethod
    def can_restart(room: ArcadeRoom, viewer: ArcadePlayer) -> bool:
        return room.phase == "finished" and room.host_id == viewer.id

    @staticmethod
    def can_update_options(room: ArcadeRoom) -> bool:
        return room.phase == Phase.LOBBY.value

    @staticmethod
    def can_start(room: ArcadeRoom, viewer: ArcadePlayer) -> bool:
        return not (
            room.options.get("shadowMerlinEnabled", False)
            and len(room.players) < 6
        )

    def start(self, room: ArcadeRoom) -> None:
        domain = self._domain(room)
        try:
            self.rules.start_game(domain, room.host_id)
        except AvalonRuleError as error:
            raise GameRuleError(str(error)) from error
        self._sync_outer(room, domain)

    def act(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        domain = self._domain(room)
        actor_id = player.id
        try:
            if action == "confirm_role":
                self.rules.confirm_role(domain, actor_id)
            elif action == "propose_team":
                self.rules.propose_team(
                    domain, actor_id, self._string_list(payload, "team_ids")
                )
            elif action == "vote_team":
                self.rules.vote_team(
                    domain, actor_id, self._boolean(payload, "approve")
                )
            elif action == "vote_mission":
                self.rules.vote_mission(
                    domain, actor_id, self._boolean(payload, "success")
                )
            elif action == "continue_round":
                self.rules.continue_after_mission(domain, actor_id)
            elif action == "exile_council_ballot":
                self.rules.submit_exile_council_ballot(
                    domain,
                    actor_id,
                    open_council=self._boolean(payload, "open_council"),
                    target_id=self._string(payload, "target_id"),
                )
            elif action in {
                "council_assassination_decision",
                "exile_council_assassination_decision",
            }:
                self.rules.submit_exile_council_assassination_decision(
                    domain,
                    actor_id,
                    self._boolean(payload, "assassinate"),
                )
            elif action in {
                "council_assassination_target",
                "exile_council_assassination_target",
            }:
                self.rules.submit_exile_council_assassination_target(
                    domain,
                    actor_id,
                    self._string(payload, "target_id"),
                )
            elif action == "lady_inspect":
                self.rules.inspect_with_lady(
                    domain, actor_id, self._string(payload, "target_id")
                )
            elif action == "lady_acknowledge":
                self.rules.acknowledge_lady(domain, actor_id)
            elif action == "assassinate":
                self.rules.assassinate(
                    domain, actor_id, self._string(payload, "target_id")
                )
            elif action == "grant_dagger":
                self.rules.grant_dagger(
                    domain, actor_id, self._string(payload, "target_id")
                )
            elif action == "dissenting_assassinate":
                self.rules.dissenting_assassinate(
                    domain, actor_id, self._string(payload, "target_id")
                )
            elif action == "early_assassinate":
                self.rules.early_assassinate(
                    domain, actor_id, self._string(payload, "target_id")
                )
            else:
                raise GameRuleError("不支持这个阿瓦隆操作")
        except AvalonRuleError as error:
            raise GameRuleError(str(error)) from error
        self._sync_outer(room, domain)

    def restart(self, room: ArcadeRoom, player: ArcadePlayer) -> None:
        domain = self._domain(room)
        try:
            self.rules.restart(domain, player.id)
        except AvalonRuleError as error:
            raise GameRuleError(str(error)) from error
        room.rematch_ready_ids.clear()
        room.undo_history.clear()
        room.pending_request = None
        self._sync_outer(room, domain)

    def disconnect_timeout(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> bool:
        return self._forfeit_player(
            room,
            player,
            reason=f"{player.name} 掉线超过 10 分钟，所属阵营视为弃权",
            ending_route="disconnect_forfeit",
        )

    def manual_forfeit(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> bool:
        return self._forfeit_player(
            room,
            player,
            reason=f"{player.name} 主动退出，所属阵营视为弃权",
            ending_route="manual_forfeit",
        )

    def _forfeit_player(
        self,
        room: ArcadeRoom,
        player: ArcadePlayer,
        *,
        reason: str,
        ending_route: str,
    ) -> bool:
        domain = self._domain(room)
        domain_player = domain.player(player.id)
        if domain_player.alignment is None:
            return False
        winner = (
            Alignment.EVIL
            if domain_player.alignment == Alignment.GOOD
            else Alignment.GOOD
        )
        domain_player.disconnect_forfeited = True
        domain_player.disconnected_at = None
        domain.winner = winner
        domain.win_reason = reason
        domain.ending_route = ending_route
        domain.phase = Phase.GAME_OVER
        domain.revision += 1
        self._sync_outer(room, domain)
        return True

    def view(
        self, room: ArcadeRoom, viewer: ArcadePlayer
    ) -> dict[str, Any]:
        domain = self._domain(room)
        return build_player_view(domain, domain.player(viewer.id), self.rules)

    def choose_bot_action(self, room: ArcadeRoom) -> BotAction | None:
        return choose_ai_action(self._domain(room), self.rules)

    def repair_restored_room(self, room: ArcadeRoom) -> bool:
        domain = self._domain(room)
        self._repair_legacy_domain(domain, reset_lock=True)
        repaired = self.rules.resolve_restored_exile_council_assassination(
            domain
        )
        if (
            not repaired
            and domain.phase == Phase.EXILE_COUNCIL_ASSASSINATION_TARGET
        ):
            ArcadeBotService().advance(
                room,
                self,
                lambda selected: self.act(
                    room,
                    room.player(selected.player_id),
                    selected.action,
                    dict(selected.payload),
                ),
            )
            repaired = domain.phase != Phase.EXILE_COUNCIL_ASSASSINATION_TARGET
        if repaired:
            self._sync_outer(room, domain)
        return repaired

    def player_result(
        self, room: ArcadeRoom, player: ArcadePlayer
    ) -> tuple[str, str, bool]:
        domain = self._domain(room)
        domain_player = domain.player(player.id)
        role = domain_player.role.value if domain_player.role else "unknown"
        alignment = (
            domain_player.alignment.value
            if domain_player.alignment is not None
            else "unknown"
        )
        return role, alignment, domain_player.alignment == domain.winner

    def persist_match(self, room: ArcadeRoom, store: Any) -> bool:
        return persist_avalon_match(self._domain(room), store)

    def _domain(self, room: ArcadeRoom) -> Room:
        domain = room.state
        if not isinstance(domain, Room):
            domain = Room(
                code=room.code,
                host_id=room.host_id,
                players=[],
                settings=GameSettings(),
            )
            room.state = domain

        self._repair_legacy_domain(domain)

        existing = {player.id: player for player in domain.players}
        synchronized_players: list[Player] = []
        for arcade_player in room.players:
            player = existing.get(arcade_player.id)
            if player is None:
                player = Player(
                    id=arcade_player.id,
                    name=arcade_player.name,
                    token_hash=arcade_player.token_hash,
                    seat=arcade_player.seat,
                    account_id=(
                        None if arcade_player.is_bot else arcade_player.account_id
                    ),
                    avatar_url=arcade_player.avatar_url,
                    is_bot=arcade_player.is_bot,
                )
            player.name = arcade_player.name
            player.token_hash = arcade_player.token_hash
            player.seat = arcade_player.seat
            player.account_id = (
                None if arcade_player.is_bot else arcade_player.account_id
            )
            player.avatar_url = arcade_player.avatar_url
            player.is_bot = arcade_player.is_bot
            player.connected = arcade_player.connected
            player.disconnected_at = arcade_player.disconnected_at
            player.disconnect_forfeited = arcade_player.disconnect_forfeited
            synchronized_players.append(player)

        domain.code = room.code
        domain.host_id = room.host_id
        domain.players = synchronized_players
        if domain.phase == Phase.LOBBY:
            self._apply_options(domain, room.options)
        domain.chat_messages = [
            ChatMessage(
                id=message.id,
                sender_id=message.sender_id,
                sender_name=message.sender_name,
                content=message.content,
                created_at=message.created_at,
            )
            for message in room.chat_messages
        ]
        domain.all_humans_offline_since = room.all_humans_offline_since
        domain.cleanup_ready = room.cleanup_ready
        domain.host_offline_since = room.host_offline_since
        return domain

    @staticmethod
    def _repair_legacy_domain(
        domain: Room,
        *,
        reset_lock: bool = False,
    ) -> None:
        if not hasattr(domain.settings, "mode"):
            domain.settings.mode = AvalonMode.STANDARD
        if not hasattr(domain.settings, "shadow_merlin_enabled"):
            domain.settings.shadow_merlin_enabled = False
        legacy_defaults: dict[str, Any] = {
            "ending_route": None,
            "dagger_candidate_ids": [],
            "dagger_target_id": None,
            "dagger_hit": None,
            "transformed_player_id": None,
            "dissenting_assassination_target_id": None,
            "shadow_merlin_transformed": False,
            "exile_council_triggered": False,
            "exile_council_open_votes": {},
            "exile_council_target_votes": {},
            "exile_council_opened": None,
            "exile_council_assassination_decisions": {},
            "exile_council_assassination_chosen": None,
            "exile_council_assassination_targets": {},
            "exile_council_assassination_target_id": None,
            "exile_council_exile_target_id": None,
            "exile_council_exile_success": None,
        }
        for field_name, default in legacy_defaults.items():
            if not hasattr(domain, field_name):
                setattr(domain, field_name, default)
        if reset_lock:
            domain.lock = asyncio.Lock()
        for player in domain.players:
            player.alignment_override = getattr(
                player, "alignment_override", None
            )
            player.disconnect_forfeited = getattr(
                player, "disconnect_forfeited", False
            )

    def _sync_outer(self, room: ArcadeRoom, domain: Room) -> None:
        allow_guests = room.options.get("allowGuests", True)
        room.state = domain
        room.host_id = domain.host_id
        room.phase = (
            "finished"
            if domain.phase == Phase.GAME_OVER
            else domain.phase.value
        )
        room.game_id = domain.game_id
        room.started_at = domain.game_started_at
        room.options = self.room_options(
            {
                "mode": domain.settings.mode.value,
                "shadowMerlinEnabled": (
                    domain.settings.shadow_merlin_enabled
                ),
                "ladyEnabled": domain.settings.lady_enabled,
                "listed": domain.settings.listed,
                "earlyAssassinationEnabled": (
                    domain.settings.early_assassination_enabled
                ),
            }
        )
        room.options["allowGuests"] = allow_guests
        room.listed = domain.settings.listed
        if domain.phase == Phase.GAME_OVER and domain.winner is not None:
            room.winner = domain.winner.value
            room.winner_player_ids = [
                player.id
                for player in domain.players
                if player.alignment == domain.winner
            ]
            room.win_reason = domain.win_reason
            room.ended_at = room.ended_at or utc_now_iso()
        else:
            room.winner = None
            room.winner_player_ids = []
            room.win_reason = None
            room.ended_at = None

    @staticmethod
    def _apply_options(domain: Room, options: dict[str, Any]) -> None:
        normalized = AvalonEngine.room_options(options)
        domain.settings.mode = AvalonMode(str(normalized["mode"]))
        domain.settings.shadow_merlin_enabled = bool(
            normalized["shadowMerlinEnabled"]
        )
        domain.settings.lady_enabled = bool(normalized["ladyEnabled"])
        domain.settings.listed = bool(normalized["listed"])
        domain.settings.early_assassination_enabled = bool(
            normalized["earlyAssassinationEnabled"]
        )

    @staticmethod
    def _string(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            raise GameRuleError("提交的数据格式不正确")
        return value

    @staticmethod
    def _boolean(payload: dict[str, Any], key: str) -> bool:
        value = payload.get(key)
        if not isinstance(value, bool):
            raise GameRuleError("提交的数据格式不正确")
        return value

    @staticmethod
    def _string_list(payload: dict[str, Any], key: str) -> list[str]:
        value = payload.get(key)
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise GameRuleError("提交的数据格式不正确")
        return value

    @classmethod
    def migrate_legacy_room(cls, legacy: Room) -> ArcadeRoom:
        engine = cls()
        engine._repair_legacy_domain(legacy, reset_lock=True)
        players = [
            ArcadePlayer(
                id=player.id,
                account_id=player.account_id or f"legacy:{player.id}",
                name=player.name,
                token_hash=player.token_hash,
                seat=player.seat,
                avatar_url=player.avatar_url,
                is_bot=player.is_bot,
                bot_difficulty="normal" if player.is_bot else None,
                connected=player.connected,
                disconnected_at=player.disconnected_at,
                disconnect_timeout_handled=player.disconnect_forfeited,
                disconnect_forfeited=player.disconnect_forfeited,
                left_room=False,
            )
            for player in legacy.players
        ]
        options = engine.room_options(
            {
                "mode": legacy.settings.mode.value,
                "shadowMerlinEnabled": (
                    getattr(
                        legacy.settings, "shadow_merlin_enabled", False
                    )
                ),
                "ladyEnabled": legacy.settings.lady_enabled,
                "listed": legacy.settings.listed,
                "earlyAssassinationEnabled": (
                    legacy.settings.early_assassination_enabled
                ),
            }
        )
        room = ArcadeRoom(
            code=legacy.code,
            game_key=engine.key,
            host_id=legacy.host_id,
            players=players,
            state=legacy,
            options=options,
            listed=legacy.settings.listed,
            phase=(
                "finished"
                if legacy.phase == Phase.GAME_OVER
                else legacy.phase.value
            ),
            revision=legacy.revision,
            game_id=legacy.game_id,
            started_at=legacy.game_started_at,
            ended_at=(
                datetime.now(timezone.utc).isoformat(timespec="seconds")
                if legacy.phase == Phase.GAME_OVER
                else None
            ),
            winner=legacy.winner.value if legacy.winner else None,
            winner_player_ids=[
                player.id
                for player in legacy.players
                if legacy.winner is not None
                and player.alignment == legacy.winner
            ],
            win_reason=legacy.win_reason,
            chat_messages=[
                ArcadeChatMessage(
                    id=message.id,
                    sender_id=message.sender_id,
                    sender_name=message.sender_name,
                    content=message.content,
                    created_at=message.created_at,
                )
                for message in legacy.chat_messages
            ],
            all_humans_offline_since=legacy.all_humans_offline_since,
            cleanup_ready=legacy.cleanup_ready,
            host_offline_since=legacy.host_offline_since,
        )
        return room

    def restore_legacy_rooms(
        self,
        state: Mapping[str, Any],
    ) -> dict[str, ArcadeRoom]:
        """Migrate rooms saved before Avalon joined the shared Arcade store."""
        saved_rooms = state.get(self.key)
        if not isinstance(saved_rooms, dict):
            return {}
        return {
            code: self.migrate_legacy_room(legacy)
            for code, legacy in saved_rooms.items()
            if isinstance(code, str) and isinstance(legacy, Room)
        }
