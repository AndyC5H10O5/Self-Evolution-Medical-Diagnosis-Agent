from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import yaml

from config.settings import CHAT_COMPLETIONS_URL, DEEPSEEK_API_KEY, MODEL_ID

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_META_FILE = PROJECT_ROOT / "skills" / "skills_meta.yaml"


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        return {}

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}

    try:
        data = json.loads(text[start:end + 1])
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


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


def _append_option(skill_key: str, field_label: str, new_option: str) -> str:
    try:
        option = _validate_new_option(new_option)
    except ValueError as exc:
        return f"Error: {exc}"

    skill_path = _load_skill_path_map().get(skill_key)
    if skill_path is None:
        return f"Error: unsupported skill_key '{skill_key}'."
    if not skill_path.exists():
        return f"Error: skill file not found: {skill_path}"

    try:
        lines = skill_path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        return f"Error: failed to read skill file: {exc}"

    prefix = f"   - {field_label}（"
    target_index = -1
    for idx, line in enumerate(lines):
        if line.startswith(prefix) and line.endswith("）"):
            target_index = idx
            break
    if target_index < 0:
        return f"Error: field_label '{field_label}' not found in {skill_key}."

    line = lines[target_index]
    options_str = line[len(prefix):-1]
    options = [item.strip() for item in options_str.split("/") if item.strip()]
    if option in options:
        return f"No update: '{option}' already exists in '{field_label}'."

    options.append(option)
    updated_line = f"{prefix}{'/'.join(options)}）"
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


def run_skill_evolution(
    skill_key: str,
    user_input: str,
    last_assistant_text: str,
    evolvable_fields: list[str],
) -> dict[str, Any]:
    """
    技能自进化总入口：先判断是否应追加，再执行追加。
    """
    decision: dict[str, Any] = {
        "should_append": False,
        "field_label": "",
        "new_option": "",
        "reason": "",
        "append_result": "",
    }

    if not user_input.strip() or not last_assistant_text.strip():
        decision["reason"] = "missing_context"
        return decision
    if not evolvable_fields:
        decision["reason"] = "no_evolvable_fields"
        return decision

    judge_system_prompt = (
        "你是一个问诊技能进化判断器。"
        "请严格输出 JSON 对象，不要输出其他文本。"
    )
    judge_user_prompt = (
        "任务：判断患者回答是否属于“已有字段的新选项”。\n"
        f"当前技能：{skill_key}\n"
        f"可进化字段：{', '.join(evolvable_fields)}\n"
        f"上一轮医生提问：{last_assistant_text}\n"
        f"本轮患者回答：{user_input}\n\n"
        "输出格式：\n"
        "{\n"
        '  "should_append": true/false,\n'
        '  "field_label": "从可进化字段中选择一个，若不追加则空字符串",\n'
        '  "new_option": "候选词或短语，若不追加则空字符串",\n'
        '  "reason": "简短判断理由"\n'
        "}\n\n"
        "规则：\n"
        "1) 仅在患者回答是某个字段的具体表达且不明显属于闲聊时才 should_append=true。\n"
        "2) new_option 必须是简短词组（2-12字），不能包含括号和斜杠。\n"
        "3) 无法确定时返回 should_append=false。"
    )

    try:
        response = httpx.post(
            CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_ID,
                "messages": [
                    {"role": "system", "content": judge_system_prompt},
                    {"role": "user", "content": judge_user_prompt},
                ],
                "max_tokens": 256,
                "temperature": 0,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        decision["reason"] = f"judge_api_error:{exc}"
        return decision

    choice = (data.get("choices") or [{}])[0]
    content = ((choice.get("message") or {}).get("content") or "").strip()
    result = _extract_json_object(content)

    should_append = bool(result.get("should_append"))
    field_label = str(result.get("field_label") or "").strip()
    new_option = str(result.get("new_option") or "").strip()
    reason = str(result.get("reason") or "").strip()

    if not should_append:
        decision["reason"] = reason or "model_reject"
        return decision
    if field_label not in evolvable_fields:
        decision["reason"] = "invalid_field_label"
        return decision
    if len(new_option) < 2 or len(new_option) > 12:
        decision["reason"] = "invalid_option_length"
        return decision
    if any(ch in new_option for ch in ("\n", "\r", "（", "）", "(", ")", "/")):
        decision["reason"] = "invalid_option_chars"
        return decision

    decision["should_append"] = True
    decision["field_label"] = field_label
    decision["new_option"] = new_option
    decision["reason"] = reason or "accepted"
    decision["append_result"] = _append_option(skill_key, field_label, new_option)
    return decision
