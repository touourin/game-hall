from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .douzero_models import POSITIONS, require_model_paths


class DouZeroRuntime:
    """Load the three official role models once and serve inference requests."""

    def __init__(self, model_paths: Mapping[str, Path], threads: int) -> None:
        _configure_inference_environment()
        import torch
        from douzero.dmc.models import model_dict

        torch.set_num_threads(threads)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
        self.torch = torch
        self.models: dict[str, Any] = {}
        for position in POSITIONS:
            model = model_dict[position]()
            state = torch.load(
                model_paths[position],
                map_location="cpu",
                weights_only=True,
            )
            if not isinstance(state, dict):
                raise RuntimeError(f"{position} 权重不是有效的 state_dict")
            model.load_state_dict(state)
            model.eval()
            self.models[position] = model

    def act(self, payload: object) -> list[int]:
        infoset = self._build_infoset(payload)
        legal_actions = infoset.legal_actions
        if len(legal_actions) == 1:
            return list(legal_actions[0])
        values = self._values([infoset])
        index = int(self.torch.argmax(values, dim=0)[0].item())
        return list(legal_actions[index])

    def opening_values(self, payload: object) -> list[float]:
        if not isinstance(payload, list) or not 1 <= len(payload) <= 256:
            raise ValueError("叫抢估值局面数量不正确")
        infosets = [self._build_infoset(item) for item in payload]
        if any(infoset.player_position != "landlord" for infoset in infosets):
            raise ValueError("叫抢估值只接受地主起始局面")
        sizes = [len(infoset.legal_actions) for infoset in infosets]
        values = self._values(infosets).flatten()
        opening_values: list[float] = []
        offset = 0
        for size in sizes:
            opening_values.append(float(values[offset : offset + size].max().item()))
            offset += size
        return opening_values

    def _values(self, infosets: list[Any]):
        from douzero.env.env import get_obs

        observations = [get_obs(infoset) for infoset in infosets]
        z_batch = self.torch.cat(
            [
                self.torch.from_numpy(observation["z_batch"]).float()
                for observation in observations
            ],
            dim=0,
        )
        x_batch = self.torch.cat(
            [
                self.torch.from_numpy(observation["x_batch"]).float()
                for observation in observations
            ],
            dim=0,
        )
        position = infosets[0].player_position
        with self.torch.inference_mode():
            return self.models[position](
                z_batch,
                x_batch,
                return_value=True,
            )["values"]

    @staticmethod
    def _build_infoset(payload: object):
        from douzero.env.game import InfoSet

        if not isinstance(payload, dict):
            raise ValueError("信息集格式不正确")
        position = payload.get("position")
        if position not in POSITIONS:
            raise ValueError("玩家位置不正确")

        infoset = InfoSet(position)
        infoset.player_hand_cards = _integer_list(
            payload.get("playerHandCards"), "手牌"
        )
        infoset.other_hand_cards = _integer_list(
            payload.get("otherHandCards"), "其余手牌"
        )
        infoset.three_landlord_cards = _integer_list(
            payload.get("threeLandlordCards"), "地主底牌"
        )
        infoset.legal_actions = _action_list(
            payload.get("legalActions"), "合法动作"
        )
        if not infoset.legal_actions:
            raise ValueError("合法动作不能为空")
        infoset.card_play_action_seq = _action_list(
            payload.get("cardPlayActionSeq"), "出牌历史"
        )
        infoset.last_move = _integer_list(
            payload.get("lastMove"), "上一手牌"
        )
        infoset.last_two_moves = _action_list(
            payload.get("lastTwoMoves"), "最近两手牌"
        )
        infoset.last_move_dict = _position_actions(
            payload.get("lastMoveDict"), "各家上一手牌"
        )
        infoset.played_cards = _position_actions(
            payload.get("playedCards"), "各家已出牌"
        )
        infoset.num_cards_left_dict = _position_counts(
            payload.get("numCardsLeftDict")
        )
        last_pid = payload.get("lastPid")
        if last_pid not in POSITIONS:
            raise ValueError("最后出牌玩家位置不正确")
        infoset.last_pid = last_pid
        bomb_num = payload.get("bombNum")
        if not isinstance(bomb_num, int) or bomb_num < 0:
            raise ValueError("炸弹数量不正确")
        infoset.bomb_num = bomb_num
        infoset.all_handcards = None
        return infoset


def _configure_inference_environment() -> None:
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    # Importing douzero.dmc.models also imports its training-only FileWriter,
    # which asks GitPython to locate a git executable. Inference never invokes
    # that writer, so a slim runtime should not need the full git package.
    os.environ["GIT_PYTHON_REFRESH"] = "quiet"


def _integer_list(value: object, label: str) -> list[int]:
    if not isinstance(value, list) or not all(isinstance(item, int) for item in value):
        raise ValueError(f"{label}格式不正确")
    return list(value)


def _action_list(value: object, label: str) -> list[list[int]]:
    if not isinstance(value, list):
        raise ValueError(f"{label}格式不正确")
    return [_integer_list(action, label) for action in value]


def _position_actions(value: object, label: str) -> dict[str, list[int]]:
    if not isinstance(value, dict) or set(value) != set(POSITIONS):
        raise ValueError(f"{label}格式不正确")
    return {
        position: _integer_list(value[position], label)
        for position in POSITIONS
    }


def _position_counts(value: object) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != set(POSITIONS):
        raise ValueError("各家剩余牌数格式不正确")
    counts: dict[str, int] = {}
    for position in POSITIONS:
        count = value[position]
        if not isinstance(count, int) or count < 0:
            raise ValueError("各家剩余牌数格式不正确")
        counts[position] = count
    return counts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Game Hall DouZero worker")
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument(
        "--check",
        action="store_true",
        help="load every model and exit without starting the worker protocol",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.threads < 1:
        raise ValueError("DouZero CPU 线程数必须大于零")
    runtime = DouZeroRuntime(require_model_paths(args.model_dir), args.threads)
    if args.check:
        print("DouZero models loaded successfully.")
        return 0
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("请求格式不正确")
            request_type = request.get("type")
            if request_type == "ping":
                response = {"ready": True}
            elif request_type == "act":
                response = {"action": runtime.act(request.get("infoset"))}
            elif request_type == "evaluate_openings":
                response = {
                    "values": runtime.opening_values(request.get("infosets"))
                }
            else:
                raise ValueError("请求类型不正确")
        except Exception as error:
            traceback.print_exc(file=sys.stderr)
            response = {"error": str(error) or type(error).__name__}
        print(
            json.dumps(response, ensure_ascii=False, separators=(",", ":")),
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
