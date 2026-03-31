from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# .../Consult_Medical_Agent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
SKILLS_META_FILE = SKILLS_DIR / "skills_meta.yaml"

_SKILLS_METADATA_CACHE: list[dict[str, Any]] | None = None

SKILL_ROUTES = {
    "abdominal_pain": {
        "label": "肚子疼",
        "file": SKILLS_DIR / "abdominal-pain" / "SKILL.md",
        "keywords": [
            "肚子疼",
            "腹痛",
            "肚子痛",
            "胃疼",
            "胃痛",
            "肚子不舒服",
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
            "呕吐",
            "干呕",
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
