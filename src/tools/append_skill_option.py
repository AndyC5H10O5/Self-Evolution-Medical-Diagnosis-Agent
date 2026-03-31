from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"

SUPPORTED_SKILL_FILES = {
    "headache": SKILLS_DIR / "headache.md",
}


def _validate_new_option(new_option: str) -> str:
    option = new_option.strip()
    if not option:
        raise ValueError("new_option is empty.")
    if len(option) < 2 or len(option) > 12:
        raise ValueError("new_option length must be between 2 and 12.")
    if any(ch in option for ch in ("\n", "\r", "（", "）", "(", ")", "/")):
        raise ValueError("new_option contains invalid characters.")
    return option


def _parse_option_line(line: str, field_label: str) -> tuple[str, list[str], str]:
    prefix = f"   - {field_label}（"
    if not line.startswith(prefix) or not line.endswith("）"):
        raise ValueError("Target line format is invalid.")

    options_str = line[len(prefix):-1]
    options = [item.strip() for item in options_str.split("/") if item.strip()]
    return prefix, options, "）"


def tool_append_skill_option(skill_key: str, field_label: str, new_option: str) -> str:
    """
    追加新选项到指定 skill 字段（最小实现：仅支持 headache.md）。
    """
    try:
        option = _validate_new_option(new_option)
    except ValueError as exc:
        return f"Error: {exc}"

    skill_path = SUPPORTED_SKILL_FILES.get(skill_key)
    if skill_path is None:
        return f"Error: unsupported skill_key '{skill_key}'."
    if not skill_path.exists():
        return f"Error: skill file not found: {skill_path}"

    try:
        lines = skill_path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return f"Error: failed to read skill file: {exc}"

    target_prefix = f"   - {field_label}（"
    target_index = -1
    for idx, line in enumerate(lines):
        if line.startswith(target_prefix) and line.endswith("）"):
            target_index = idx
            break

    if target_index < 0:
        return f"Error: field_label '{field_label}' not found in {skill_key}."

    try:
        prefix, options, suffix = _parse_option_line(lines[target_index], field_label)
    except ValueError as exc:
        return f"Error: {exc}"

    if option in options:
        return f"No update: '{option}' already exists in '{field_label}'."

    options.append(option)
    updated_line = f"{prefix}{'/'.join(options)}{suffix}"
    lines[target_index] = updated_line

    try:
        skill_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as exc:
        return f"Error: failed to write skill file: {exc}"

    relative_path = skill_path.relative_to(PROJECT_ROOT)
    return (
        f"Successfully appended option '{option}' to '{field_label}' in {relative_path}. "
        f"Updated line: {updated_line}"
    )


APPEND_SKILL_OPTION_TOOL = {
    "name": "append_skill_option",
    "description": (
        "Append a new patient expression into an existing skill question options list. "
        "Use this only when the expression is clinically meaningful and not already listed."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "skill_key": {
                "type": "string",
                "description": "Target skill key, minimal version supports only 'headache'.",
            },
            "field_label": {
                "type": "string",
                "description": "Question field label, e.g. 头痛性质.",
            },
            "new_option": {
                "type": "string",
                "description": "New option text from patient answer, e.g. 头部沉重.",
            },
        },
        "required": ["skill_key", "field_label", "new_option"],
    },
}
