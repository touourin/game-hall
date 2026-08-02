from pydantic import BaseModel, Field

from .models import AvalonMode


class JoinPayload(BaseModel):
    room_code: str = Field(min_length=4, max_length=8)


class ResumePayload(BaseModel):
    room_code: str = Field(min_length=4, max_length=8)
    token: str = Field(min_length=16, max_length=256)


class LadySettingPayload(BaseModel):
    enabled: bool


class ListedSettingPayload(BaseModel):
    listed: bool


class EarlyAssassinationSettingPayload(BaseModel):
    enabled: bool


class ModeSettingPayload(BaseModel):
    mode: AvalonMode


class TeamPayload(BaseModel):
    team_ids: list[str] = Field(min_length=1, max_length=5)


class TeamVotePayload(BaseModel):
    approve: bool


class MissionVotePayload(BaseModel):
    success: bool


class TargetPayload(BaseModel):
    target_id: str = Field(min_length=1, max_length=64)


class ChatPayload(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
