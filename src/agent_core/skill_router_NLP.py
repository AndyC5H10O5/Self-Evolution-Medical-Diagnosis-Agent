from __future__ import annotations

import json
from typing import Any

import httpx

from agent_core.skill_router import (
    build_metadata_candidates,
    build_metadata_match_prompt,
    validate_metadata_selected_skill,
)
from config.settings import CHAT_COMPLETIONS_URL, DEEPSEEK_API_KEY, MODEL_ID


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


def detect_skill_key_by_metadata(user_input: str) -> str | None:
    candidates = build_metadata_candidates(user_input)
    if not candidates:
        return None

    judge_system_prompt = (
        "你是症状技能路由器。"
        "请基于候选技能的 use_when，输出最匹配的单一 skill_key。"
        "若不匹配，返回 none。仅输出 JSON。"
    )
    judge_user_prompt = build_metadata_match_prompt(user_text=user_input, candidates=candidates)

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
    except Exception:
        return None

    choice = (data.get("choices") or [{}])[0]
    content = ((choice.get("message") or {}).get("content") or "").strip()
    result = _extract_json_object(content)
    selected_skill_key = str(result.get("skill_key") or "").strip()
    return validate_metadata_selected_skill(selected_skill_key, candidates)
