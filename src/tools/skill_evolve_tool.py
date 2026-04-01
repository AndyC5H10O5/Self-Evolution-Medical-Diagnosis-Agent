from __future__ import annotations

from pathlib import Path

import yaml

from agent_core.skill_router import get_evolvable_fields

# 项目根目录: .../Consult_Medical_Agent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_META_FILE = PROJECT_ROOT / "skills" / "skills_meta.yaml"


def _load_skill_path_map() -> dict[str, Path]:
    if not SKILLS_META_FILE.exists():
        return {}
    try:
        raw = yaml.safe_load(SKILLS_META_FILE.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

    items = raw.get("skills")
    if not isinstance(items, list):
        return {}

    path_map: dict[str, Path] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        skill_key = str(item.get("skill_key", "")).strip()
        rel_path = str(item.get("path", "")).strip()
        if not skill_key or not rel_path:
            continue
        path_map[skill_key] = (PROJECT_ROOT / rel_path).resolve()
    return path_map


def _validate_new_option(new_option: str) -> str:
    option = new_option.strip()
    if not option:
        raise ValueError("new_option is empty.")
    if len(option) < 2 or len(option) > 12:
        raise ValueError("new_option length must be between 2 and 12.")
    if any(ch in option for ch in ("\n", "\r", "（", "）", "(", ")", "/")):
        raise ValueError("new_option contains invalid characters.")
    return option


def tool_skill_evolve(skill_key: str, field_label: str, new_option: str) -> str:
    """
    追加症状 Skill 里的字段选项.
    由主模型按需调用, 不做额外模型判别.
    """
    key = (skill_key or "").strip()
    field = (field_label or "").strip()
    if not key:
        return "Error: skill_key is empty."
    if not field:
        return "Error: field_label is empty."

    allowed_fields = get_evolvable_fields(key)
    if not allowed_fields:
        return f"Error: skill '{key}' has no evolvable fields."
    if field not in allowed_fields:
        return (
            f"Error: field_label '{field}' is not evolvable for skill '{key}'. "
            f"Allowed fields: {', '.join(allowed_fields)}"
        )

    try:
        option = _validate_new_option(new_option)
    except ValueError as exc:
        return f"Error: {exc}"

    skill_path = _load_skill_path_map().get(key)
    if skill_path is None:
        return f"Error: unsupported skill_key '{key}'."
    if not skill_path.exists():
        return f"Error: skill file not found: {skill_path}"

    try:
        lines = skill_path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return f"Error: failed to read skill file: {exc}"

    prefix = f"   - {field}（"
    target_index = -1
    for idx, line in enumerate(lines):
        if line.startswith(prefix) and line.endswith("）"):
            target_index = idx
            break
    if target_index < 0:
        return f"Error: field_label '{field}' not found in {key}."

    line = lines[target_index]
    options_str = line[len(prefix):-1]
    options = [item.strip() for item in options_str.split("/") if item.strip()]
    if option in options:
        return f"No update: '{option}' already exists in '{field}'."

    options.append(option)
    updated_line = f"{prefix}{'/'.join(options)}）"
    lines[target_index] = updated_line

    try:
        skill_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as exc:
        return f"Error: failed to write skill file: {exc}"

    relative_path = skill_path.relative_to(PROJECT_ROOT)
    return (
        f"Successfully appended option '{option}' to '{field}' in {relative_path}. "
        f"Updated line: {updated_line}"
    )


SKILL_EVOLVE_TOOL = {
    "name": "skill_evolve",
    "description": (
        "Append a new option to an evolvable field in a symptom skill file. "
        "Evolve the active symptom skill file: append one new option to an evolvable field. "
        "Call only when the patient's latest answer is a clear, concise new option "
        "for the active skill and target field."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "skill_key": {
                "type": "string",
                "description": "Active symptom skill key, for example: headache.",
            },
            "field_label": {
                "type": "string",
                "description": "One evolvable field label under the active skill.",
            },
            "new_option": {
                "type": "string",
                "description": (
                    "New short option phrase from patient answer (2-12 chars), "
                    "without brackets or '/'."
                ),
            },
        },
        "required": ["skill_key", "field_label", "new_option"],
    },
}
