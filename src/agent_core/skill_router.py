from __future__ import annotations

from pathlib import Path

# .../Consult_Medical_Agent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"

SKILL_ROUTES = {
    "abdominal_pain": {
        "label": "肚子疼",
        "file": SKILLS_DIR / "abdominal_pain.md",
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
        "file": SKILLS_DIR / "headache.md",
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
        "file": SKILLS_DIR / "nausea.md",
        "keywords": [
            "恶心",
            "想吐",
            "反胃",
            "呕吐",
            "干呕",
        ],
    },
}


def detect_skill_key(user_text: str) -> str | None:
    text = user_text.strip().lower()
    for skill_key, route in SKILL_ROUTES.items():
        for keyword in route["keywords"]:
            if keyword.lower() in text:
                return skill_key
    return None


def get_skill_label(skill_key: str) -> str:
    route = SKILL_ROUTES.get(skill_key)
    if route is None:
        return skill_key
    return str(route["label"])


def load_skill_prompt(skill_key: str) -> str:
    route = SKILL_ROUTES.get(skill_key)
    if route is None:
        return ""

    file_path = route["file"]
    try:
        return file_path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def get_evolvable_fields(skill_key: str) -> list[str]:
    route = SKILL_ROUTES.get(skill_key)
    if route is None:
        return []
    fields = route.get("evolvable_fields")
    if not isinstance(fields, list):
        return []
    return [str(field) for field in fields]
