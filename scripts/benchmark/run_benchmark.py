from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# 直接改这里即可（无需命令行参数）
# ---------------------------------------------------------------------------
RUN_MODE = "evolve"  # "baseline" | "evolve"
# 项目根目录（.../Consult_Medical_Agent）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CASES_CSV = _PROJECT_ROOT / "benchmark" / "eval_cases.csv"
# 留空则自动: benchmark/runs/{时间戳}_{mode}/raw_results.jsonl
OUTPUT_JSONL: Path | None = None
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
MODEL_ID = os.getenv("MODEL_ID", "deepseek-chat")
TEMPERATURE = 0.0


def _load_cases(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _build_prompt(case: dict[str, str]) -> str:
    return (
        "你是问诊自进化判别器。请输出JSON，字段包括："
        "should_evolve(boolean), field_label(string), new_option(string), reason(string)。\n"
        f"当前skill_key: {case.get('skill_key','')}\n"
        f"上一问字段: {case.get('last_assistant_question_field','')}\n"
        f"患者回答: {case.get('user_turn','')}\n"
        "规则：仅当回答是该字段的新选项时should_evolve=true；"
        "若是字母选择、已有选项或同义复述则false。"
    )


def _call_openai_compatible(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"
    resp = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是严格JSON输出助手。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": 256,
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    data = resp.json()
    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        content = content[start : end + 1]
    try:
        return json.loads(content)
    except Exception:
        return {"should_evolve": False, "field_label": "", "new_option": "", "reason": f"json_parse_error:{content}"}


def _baseline_prediction() -> dict[str, Any]:
    return {
        "should_evolve": False,
        "field_label": "",
        "new_option": "",
        "reason": "baseline_disabled",
    }


def main() -> None:
    if RUN_MODE not in ("baseline", "evolve"):
        raise SystemExit(f"RUN_MODE 必须是 baseline 或 evolve，当前: {RUN_MODE!r}")

    if RUN_MODE == "evolve" and not DEEPSEEK_API_KEY:
        raise SystemExit("Evolve 模式需要 API Key：在 .env 里配置 DEEPSEEK_API_KEY，或改代码里 DEEPSEEK_API_KEY。")

    cases = _load_cases(CASES_CSV)
    if OUTPUT_JSONL is not None:
        out_path = Path(OUTPUT_JSONL)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = _PROJECT_ROOT / "benchmark" / "runs" / f"{ts}_{RUN_MODE}" / "raw_results.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for case in cases:
            if RUN_MODE == "baseline":
                pred = _baseline_prediction()
            else:
                pred = _call_openai_compatible(
                    base_url=DEEPSEEK_BASE_URL,
                    api_key=DEEPSEEK_API_KEY,
                    model=MODEL_ID,
                    prompt=_build_prompt(case),
                    temperature=TEMPERATURE,
                )

            row = {
                "sample_id": case.get("sample_id", ""),
                "mode": RUN_MODE,
                "gold": {
                    "should_evolve": str(case.get("should_evolve_gold", "0")).strip() == "1",
                    "field_label": case.get("gold_field_label", ""),
                    "new_option": case.get("gold_new_option", ""),
                },
                "prediction": {
                    "should_evolve": bool(pred.get("should_evolve")),
                    "field_label": str(pred.get("field_label", "")),
                    "new_option": str(pred.get("new_option", "")),
                    "reason": str(pred.get("reason", "")),
                },
                "meta": {
                    "skill_key": case.get("skill_key", ""),
                    "last_assistant_question_field": case.get("last_assistant_question_field", ""),
                    "user_turn": case.get("user_turn", ""),
                    "is_existing_option_or_synonym": case.get("is_existing_option_or_synonym", ""),
                },
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Benchmark results written to: {out_path}")


if __name__ == "__main__":
    main()
