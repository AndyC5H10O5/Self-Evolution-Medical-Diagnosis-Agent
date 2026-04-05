from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import httpx

# 允许直接运行 `python src/evolve_core/main.py`
SRC_ROOT = Path(__file__).resolve().parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_core.skill_router import get_evolvable_fields, load_skill_prompt
from config.settings import CHAT_COMPLETIONS_URL, DEEPSEEK_API_KEY, MODEL_ID
from config.sys_prompts import EVOLVE_SYSTEM_PROMPT
from evolve_core.schemas import EvolutionCandidate, EvolutionJudgeResult
from evolve_core.worker import FileQueueConsumer
from tools.skill_evolve_tool import tool_skill_evolve
from utils.console import DIM, RESET, YELLOW, print_info


def _build_prompt(candidate: EvolutionCandidate) -> str:
    evolvable_fields = get_evolvable_fields(candidate.skill_key)
    fields_text = ", ".join(evolvable_fields) if evolvable_fields else "（无）"
    skill_text = load_skill_prompt(candidate.skill_key) or "（skill内容为空）"
    return (
        "你将判断此候选是否应触发技能进化。\n\n"
        f"当前 skill_key: {candidate.skill_key}\n"
        f"允许进化字段: {fields_text}\n"
        f"候选 field_label: {candidate.field_label}\n"
        f"候选 option: {candidate.candidate_option}\n"
        f"上一问字段(参考): {candidate.last_assistant_question_field}\n"
        f"患者回答原文: {candidate.user_turn}\n\n"
        "以下是当前 skill 文本，请基于其中字段与选项判断：\n"
        f"{skill_text}\n\n"
        "仅输出 JSON："
        '{"should_evolve":false,"field_label":"","new_option":"","reason":""}'
    )


def _judge_with_llm(candidate: EvolutionCandidate) -> EvolutionJudgeResult:
    prompt = _build_prompt(candidate)
    response = httpx.post(
        CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": EVOLVE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 512,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()
    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    start = content.find("{")
    end = content.rfind("}")
    parsed: dict[str, Any] = {}
    if start >= 0 and end > start:
        try:
            parsed = json.loads(content[start : end + 1])
        except Exception:
            parsed = {"should_evolve": False, "field_label": "", "new_option": "", "reason": f"json_parse_error:{content}"}
    else:
        parsed = {"should_evolve": False, "field_label": "", "new_option": "", "reason": f"json_parse_error:{content}"}
    return EvolutionJudgeResult.from_dict(parsed, raw_text=content)


def _handle_candidate(candidate: EvolutionCandidate) -> None:
    print_info(
        f"[evolve_queue] consume {candidate.event_id} "
        f"| skill_key={candidate.skill_key} | field={candidate.field_label} | option={candidate.candidate_option}"
    )
    try:
        judge = _judge_with_llm(candidate)
    except Exception as exc:
        print_info(f"[evolve_error] {candidate.event_id} | llm_error={exc}")
        return

    field_label = judge.field_label or candidate.field_label
    new_option = judge.new_option or candidate.candidate_option
    reason = judge.reason or "-"
    if not judge.should_evolve:
        print_info(
            f"[evolve_skip] {candidate.event_id} "
            f"| field={field_label} | option={new_option} | reason={reason}"
        )
        return

    result = tool_skill_evolve(
        skill_key=candidate.skill_key,
        field_label=field_label,
        new_option=new_option,
    )
    print_info(
        f"[evolve_apply] {candidate.event_id} "
        f"| field={field_label} | option={new_option} | result={result}"
    )


def main() -> None:
    if not DEEPSEEK_API_KEY:
        print(f"{YELLOW}Error: DEEPSEEK_API_KEY 未设置.{RESET}")
        print(f"{DIM}将 .env.example 复制为 .env 并填入你的 key.{RESET}")
        sys.exit(1)

    print_info("=" * 60)
    print_info(f"  Evolver Model: {MODEL_ID}")
    print_info("  Queue: runtime/evolution/candidates.jsonl")
    print_info("  Ctrl+C 退出")
    print_info("=" * 60)
    consumer = FileQueueConsumer(poll_seconds=1.0)
    try:
        consumer.run_forever(_handle_candidate)
    except KeyboardInterrupt:
        print_info("evolver stopped.")


if __name__ == "__main__":
    main()
