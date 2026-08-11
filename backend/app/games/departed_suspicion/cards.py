from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EquipmentDefinition:
    id: str
    number: int
    name: str
    english_name: str
    expansion: str
    timing: str
    description: str
    persistent: bool = False
    requires_cover: bool = False

    def as_dict(self, *, available: bool = True) -> dict[str, object]:
        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "englishName": self.english_name,
            "expansion": self.expansion,
            "timing": self.timing,
            "description": self.description,
            "persistent": self.persistent,
            "requiresCover": self.requires_cover,
            "available": available,
        }


def _card(
    number: int,
    card_id: str,
    name: str,
    english_name: str,
    expansion: str,
    timing: str,
    description: str,
    *,
    persistent: bool = False,
    requires_cover: bool = False,
) -> EquipmentDefinition:
    return EquipmentDefinition(
        id=card_id,
        number=number,
        name=name,
        english_name=english_name,
        expansion=expansion,
        timing=timing,
        description=description,
        persistent=persistent,
        requires_cover=requires_cover,
    )


EQUIPMENT_CARDS: tuple[EquipmentDefinition, ...] = (
    _card(1, "blackmail", "勒索信", "Blackmail", "base", "anytime", "交换两名其他存活玩家各一张底细；牌的公开状态不变。"),
    _card(2, "coffee", "咖啡", "Coffee", "base", "other_turn", "当前玩家结束回合后，你立刻获得一个完整回合；该回合结束后恢复原回合顺序。"),
    _card(3, "defibrillator", "除颤器", "Defibrillator", "base", "anytime", "复活一名已经出局的非领袖玩家。"),
    _card(4, "evidence_bag", "证物袋", "Evidence Bag", "base", "anytime", "把一名玩家手中的装备交给另一名不是你的玩家。"),
    _card(5, "flashbang", "闪光弹", "Flashbang", "base", "anytime", "混洗一名玩家的三张底细，公开状态不变并清除位置记忆。"),
    _card(6, "k9_unit", "警犬队", "K-9 Unit", "base", "anytime", "令一名持枪玩家立即丢枪；可取消尚未结算的射击。"),
    _card(7, "metal_detector", "金属探测器", "Metal Detector", "base", "anytime", "依次调查每名持枪玩家的一张暗置底细。"),
    _card(8, "planted_evidence", "栽赃证据", "Planted Evidence", "base", "anytime", "目标普通正直/腐败底细的阵营计算永久互换。", persistent=True),
    _card(9, "polygraph", "测谎仪", "Polygraph", "base", "anytime", "你调查目标全部暗牌，随后目标调查你的全部暗牌。"),
    _card(10, "report_audit", "报告审查", "Report Audit", "base", "anytime", "每名仍有暗牌的玩家各自选择一张永久公开。"),
    _card(11, "restraining_order", "限制令", "Restraining Order", "base", "shoot_response", "射手必须改瞄另一名合法目标并完成射击。"),
    _card(12, "smoke_grenade", "烟雾弹", "Smoke Grenade", "base", "anytime", "永久反转当前回合方向。"),
    _card(13, "surveillance_camera", "监控摄像头", "Surveillance Camera", "base", "after_investigate", "紧接正常调查行动后，把刚调查的底细永久公开。"),
    _card(14, "taser", "电击枪", "Taser", "base", "own_turn", "夺取另一名玩家的枪并立刻选择合法瞄准目标。"),
    _card(15, "truth_serum", "吐真剂", "Truth Serum", "base", "anytime", "目标从自己的暗牌中选择一张永久公开。"),
    _card(16, "wiretap", "窃听器", "Wiretap", "base", "anytime", "分别调查两名不同玩家的一张暗置底细。"),
    _card(17, "classified_orders", "机密指令", "Classified Orders", "bombers", "shoot_response", "指定另一名玩家替射手决定新的合法目标并立即射击。"),
    _card(18, "fake_id", "假证件", "Fake ID", "bombers", "anytime", "交换两张公开、非领袖的正直/腐败底细。"),
    _card(19, "fingerprint_kit", "指纹工具", "Fingerprint Kit", "bombers", "anytime", "调查一张底细；若再公开自己一张暗牌，本牌回到手中。"),
    _card(20, "grenade", "手榴弹", "Grenade", "bombers", "anytime", "第一位接收者下回合末传递；第二位接收者下回合末中枪。", persistent=True),
    _card(21, "holster", "枪套", "Holster", "bombers", "own_shoot", "自己的射击结算前改变瞄准目标。"),
    _card(22, "concussion_grenade", "震撼弹", "Concussion Grenade", "undercover", "anytime", "所有持枪玩家立即丢枪；可取消尚未结算的射击。"),
    _card(23, "crutches", "拐杖", "Crutches", "undercover", "anytime", "复活另一名非领袖；此后该玩家只能执行获取装备行动。", persistent=True),
    _card(24, "disguise", "伪装", "Disguise", "undercover", "anytime", "本局余下时间任何人都不能调查目标。", persistent=True),
    _card(25, "helmet", "头盔", "Helmet", "undercover", "self_shot", "取消自己即将受到的一次中枪；射手仍丢枪且不能改选行动。"),
    _card(26, "inspection_gloves", "搜查手套", "Inspection Gloves", "undercover", "anytime", "目标弃装备，或向所有人展示全部暗牌后重新暗置。"),
    _card(27, "key", "钥匙", "Key", "undercover", "anytime", "目标每回合获得一次不占正常行动的额外调查。", persistent=True),
    _card(28, "med_kit", "医疗包", "Med Kit", "undercover", "anytime", "移除探员或头目领袖牌上的受伤标记。"),
    _card(29, "mobile_detonator", "移动引爆器", "Mobile Detonator", "undercover", "post_shot", "自己中枪且尚未产生胜者时，使另一名玩家也中枪。"),
    _card(30, "new_assignment", "新任务", "New Assignment", "undercover", "anytime", "交换两名玩家的卧底牌，原遮蔽位置不变。", requires_cover=True),
    _card(31, "security_wand", "安检棒", "Security Wand", "undercover", "anytime", "调查另一名玩家一张牌；可把自己一张公开底细重新暗置。"),
    _card(32, "sunglasses", "太阳镜", "Sunglasses", "undercover", "anytime", "把任意两张公开底细重新暗置。"),
    _card(33, "thumbprint_scanner", "指纹扫描器", "Thumbprint Scanner", "undercover", "post_reveal", "玩家中枪并公开底细后，可用自己一张底细交换其一张普通底细。"),
)

EQUIPMENT_BY_ID = {card.id: card for card in EQUIPMENT_CARDS}
BASE_EQUIPMENT_IDS = tuple(
    card.id for card in EQUIPMENT_CARDS if card.expansion == "base"
)
BOMBERS_EQUIPMENT_IDS = tuple(
    card.id
    for card in EQUIPMENT_CARDS
    if card.expansion in {"base", "bombers"}
)
