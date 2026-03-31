from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from utils.console import print_info


# .../Consult_Medical_Agent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
SKILLS_META_FILE = SKILLS_DIR / "skills_meta.yaml"

_SKILLS_METADATA_CACHE: list[dict[str, Any]] | None = None

SKILL_ROUTES = {
    "abdominal_pain": {
        "label": "肚子痛",
        "file": SKILLS_DIR / "abdominal-pain" / "SKILL.md",
        "keywords": [
            "肚子痛",
            "腹痛",
            "胃疼",
            "胃痛",
            "肚子绞痛",
        ],
    },
    "headache": {
        "label": "头痛",
        "file": SKILLS_DIR / "headache" / "SKILL.md",
        "evolvable_fields": ["头痛部位", "头痛性质", "伴随症状"],
        "keywords": [
            "头痛",
            "头疼",
            "偏头痛",
            "脑袋疼",
            "头一阵一阵疼",
        ],
    },
    "nausea": {
        "label": "恶心",
        "file": SKILLS_DIR / "nausea" / "SKILL.md",
        "keywords": [
            "恶心",
            "想吐",
            "反胃",
            "干呕",
            "胃里翻腾",
        ],
    },
    "insomnia": {
        "label": "失眠",
        "file": SKILLS_DIR / "insomnia" / "SKILL.md",
        "keywords": [
            "失眠",
            "睡不着",
            "入睡困难",
            "总醒",
            "早醒",
        ],
    },
    "tinnitus": {
        "label": "耳鸣",
        "file": SKILLS_DIR / "tinnitus" / "SKILL.md",
        "keywords": [
            "耳鸣",
            "耳朵嗡嗡",
            "耳朵响",
            "听到鸣响",
            "耳内噪音",
        ],
    },
    "eye_pain": {
        "label": "眼痛",
        "file": SKILLS_DIR / "eye-pain" / "SKILL.md",
        "keywords": [
            "眼痛",
            "眼睛疼",
            "眼睛刺痛",
            "眼球痛",
            "眼眶痛",
        ],
    },
    "runny_nose": {
        "label": "流鼻涕",
        "file": SKILLS_DIR / "runny-nose" / "SKILL.md",
        "keywords": [
            "流鼻涕",
            "鼻涕多",
            "鼻子老流水",
            "清鼻涕",
            "鼻塞流涕",
        ],
    },
    "chest_pain": {
        "label": "胸痛",
        "file": SKILLS_DIR / "chest-pain" / "SKILL.md",
        "keywords": [
            "胸痛",
            "胸口痛",
            "胸闷痛",
            "胸口压痛",
            "胸前区疼",
        ],
    },
    "heart_pain": {
        "label": "心痛",
        "file": SKILLS_DIR / "heart-pain" / "SKILL.md",
        "keywords": [
            "心痛",
            "心口痛",
            "心前区痛",
            "心脏疼",
            "心口发紧",
        ],
    },
    "sore_throat": {
        "label": "喉咙痛",
        "file": SKILLS_DIR / "sore-throat" / "SKILL.md",
        "keywords": [
            "喉咙痛",
            "嗓子痛",
            "咽痛",
            "吞咽痛",
            "咽喉疼",
        ],
    },
    "cough": {
        "label": "咳嗽",
        "file": SKILLS_DIR / "cough" / "SKILL.md",
        "keywords": [
            "咳嗽",
            "一直咳",
            "干咳",
            "咳痰",
            "夜咳",
        ],
    },
    "diarrhea": {
        "label": "腹泻",
        "file": SKILLS_DIR / "diarrhea" / "SKILL.md",
        "keywords": [
            "腹泻",
            "拉肚子",
            "大便稀",
            "水样便",
            "一天拉很多次",
        ],
    },
    "vomiting": {
        "label": "呕吐",
        "file": SKILLS_DIR / "vomiting" / "SKILL.md",
        "keywords": [
            "呕吐",
            "吐了",
            "一直吐",
            "干呕",
            "反复呕吐",
        ],
    },
    "joint_pain": {
        "label": "关节痛",
        "file": SKILLS_DIR / "joint-pain" / "SKILL.md",
        "keywords": [
            "关节痛",
            "膝盖痛",
            "手指关节痛",
            "关节酸痛",
            "关节肿痛",
        ],
    },
    "waist_pain": {
        "label": "腰痛",
        "file": SKILLS_DIR / "waist-pain" / "SKILL.md",
        "keywords": [
            "腰痛",
            "腰疼",
            "腰酸",
            "腰部疼痛",
            "弯腰就痛",
        ],
    },
    "back_pain": {
        "label": "背痛",
        "file": SKILLS_DIR / "back-pain" / "SKILL.md",
        "keywords": [
            "背痛",
            "后背痛",
            "背部疼",
            "背酸痛",
            "上背痛",
        ],
    },
    "leg_pain": {
        "label": "腿痛",
        "file": SKILLS_DIR / "leg-pain" / "SKILL.md",
        "keywords": [
            "腿痛",
            "腿疼",
            "小腿痛",
            "大腿痛",
            "腿酸痛",
        ],
    },
    "fever": {
        "label": "发烧",
        "file": SKILLS_DIR / "fever" / "SKILL.md",
        "keywords": [
            "发烧",
            "发热",
            "体温高",
            "低烧",
            "高烧",
        ],
    },
    "fatigue": {
        "label": "疲劳",
        "file": SKILLS_DIR / "fatigue" / "SKILL.md",
        "keywords": [
            "疲劳",
            "乏力",
            "没精神",
            "很累",
            "总是疲惫",
        ],
    },
    "acne": {
        "label": "痤疮",
        "file": SKILLS_DIR / "acne" / "SKILL.md",
        "keywords": [
            "痤疮",
            "青春痘",
            "长痘",
            "粉刺",
            "脸上起痘",
        ],
    },
    "weight_gain": {
        "label": "体重增加",
        "file": SKILLS_DIR / "weight-gain" / "SKILL.md",
        "keywords": [
            "体重增加",
            "长胖",
            "体重上涨",
            "最近胖了",
            "增重",
        ],
    },
}


def load_skills_metadata(force_reload: bool = False) -> list[dict[str, Any]]:
    global _SKILLS_METADATA_CACHE

    if _SKILLS_METADATA_CACHE is not None and not force_reload:
        return _SKILLS_METADATA_CACHE

    if not SKILLS_META_FILE.exists():
        _SKILLS_METADATA_CACHE = []
        return _SKILLS_METADATA_CACHE

    try:
        raw = yaml.safe_load(SKILLS_META_FILE.read_text(encoding="utf-8")) or {}
    except Exception:
        _SKILLS_METADATA_CACHE = []
        return _SKILLS_METADATA_CACHE

    items = raw.get("skills")
    if not isinstance(items, list):
        _SKILLS_METADATA_CACHE = []
        return _SKILLS_METADATA_CACHE

    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        skill_key = str(item.get("skill_key", "")).strip()
        rel_path = str(item.get("path", "")).strip()
        if not skill_key or not rel_path:
            continue
        absolute_path = (PROJECT_ROOT / rel_path).resolve()
        normalized.append({
            "skill_key": skill_key,
            "name": str(item.get("name", "")).strip(),
            "label": str(item.get("label", "")).strip(),
            "path": absolute_path,
            "keywords": [str(keyword).strip() for keyword in (item.get("keywords") or []) if str(keyword).strip()],
            "use_when": str(item.get("use_when", "")).strip(),
            "evolvable_fields": [
                str(field).strip()
                for field in (item.get("evolvable_fields") or [])
                if str(field).strip()
            ],
        })

    _SKILLS_METADATA_CACHE = normalized
    return _SKILLS_METADATA_CACHE


def build_metadata_candidates(user_text: str) -> list[dict[str, Any]]:
    _ = user_text
    metadata = load_skills_metadata()
    if not metadata:
        return []
    # 语义回退阶段不再使用关键词打分，直接把全部技能作为候选交给模型。
    return metadata


def build_metadata_match_prompt(user_text: str, candidates: list[dict[str, Any]]) -> str:
    lines = [
        "请根据患者描述，从候选技能中选择最匹配的一个 skill_key。",
        "若都不匹配，返回 none。",
        "",
        f"患者描述: {user_text}",
        "",
        "候选技能:",
    ]

    for idx, candidate in enumerate(candidates, start=1):
        lines.append(
            f"{idx}. skill_key={candidate['skill_key']}, label={candidate.get('label', '')}, "
            f"use_when={candidate.get('use_when', '')}"
        )

    lines.extend([
        "",
        "输出 JSON：",
        '{"skill_key":"候选skill_key或none","reason":"简短理由"}',
    ])
    return "\n".join(lines)


def validate_metadata_selected_skill(
    selected_skill_key: str,
    candidates: list[dict[str, Any]],
) -> str | None:
    key = selected_skill_key.strip()
    if not key or key == "none":
        return None
    allowed = {str(item["skill_key"]) for item in candidates}
    return key if key in allowed else None


def detect_skill_key(user_text: str) -> str | None:
    text = user_text.strip().lower()
    for skill_key, route in SKILL_ROUTES.items():
        for keyword in route["keywords"]:
            if keyword.lower() in text:
                print_info(f"[skill_router: keyword_hit] {keyword}")
                return skill_key
    return None


def _get_route(skill_key: str) -> dict[str, Any] | None:
    route = SKILL_ROUTES.get(skill_key)
    if route is not None:
        return route

    for item in load_skills_metadata():
        if item.get("skill_key") == skill_key:
            return {
                "label": item.get("label") or skill_key,
                "file": item.get("path"),
                "evolvable_fields": item.get("evolvable_fields", []),
            }
    return None


def get_skill_label(skill_key: str) -> str:
    route = _get_route(skill_key)
    if route is None:
        return skill_key
    return str(route["label"])


def load_skill_prompt(skill_key: str) -> str:
    route = _get_route(skill_key)
    if route is None:
        return ""

    file_path = route["file"]
    try:
        return file_path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def get_evolvable_fields(skill_key: str) -> list[str]:
    route = _get_route(skill_key)
    if route is None:
        return []
    fields = route.get("evolvable_fields")
    if not isinstance(fields, list):
        return []
    return [str(field) for field in fields]
