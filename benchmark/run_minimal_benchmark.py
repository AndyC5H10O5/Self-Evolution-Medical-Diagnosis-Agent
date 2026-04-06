from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config.settings import MODEL_ID
from evolve_core.main import _handle_candidate, _judge_with_llm
from evolve_core.schemas import EvolutionCandidate
from evolve_core.worker import FileQueueConsumer, QUEUE_FILE, STATE_FILE, enqueue_candidate
from tools.skill_evolve_tool import _load_skill_path_map


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal benchmark for evolver.")
    parser.add_argument(
        "--train",
        type=Path,
        default=PROJECT_ROOT / "benchmark" / "cases" / "minimal_train.jsonl",
        help="Train jsonl path.",
    )
    parser.add_argument(
        "--test",
        type=Path,
        default=PROJECT_ROOT / "benchmark" / "cases" / "minimal_test.jsonl",
        help="Test jsonl path.",
    )
    parser.add_argument("--skill-key", type=str, default="headache", help="Target skill key.")
    parser.add_argument("--field-label", type=str, default="头痛性质", help="Target field label.")
    parser.add_argument(
        "--consume-timeout-seconds",
        type=float,
        default=120.0,
        help="Timeout for queue consumption.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=0.5,
        help="Poll interval while consuming queue.",
    )
    parser.add_argument(
        "--no-reset-consumer-state",
        action="store_false",
        dest="reset_consumer_state",
        help="Do not reset consumer state before enqueueing train cases.",
    )
    parser.set_defaults(reset_consumer_state=True)
    return parser.parse_args()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"JSONL not found: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        rows.append(json.loads(text))
    return rows


def _required_str(raw: dict[str, Any], key: str) -> str:
    value = str(raw.get(key, "")).strip()
    if not value:
        raise ValueError(f"Missing required field '{key}' in case: {raw}")
    return value


def _to_candidate(raw: dict[str, Any], source: str = "benchmark_minimal") -> EvolutionCandidate:
    return EvolutionCandidate.create(
        source=source,
        skill_key=_required_str(raw, "skill_key"),
        field_label=_required_str(raw, "field_label"),
        user_turn=_required_str(raw, "user_turn"),
        candidate_option=_required_str(raw, "candidate_option"),
        last_assistant_question_field=str(raw.get("last_assistant_question_field", "")).strip(),
    )


def _count_queue_lines() -> int:
    if not QUEUE_FILE.exists():
        return 0
    return len(QUEUE_FILE.read_text(encoding="utf-8").splitlines())


def _set_consumer_state(last_line: int) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps({"last_line": max(0, int(last_line))}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _normalize_slot(text: str) -> str:
    value = (text or "").strip().replace(" ", "").replace("\u3000", "")
    value = value.replace("，", ",").replace("；", ";").replace("：", ":")
    return value


def _get_field_snapshot(skill_key: str, field_label: str) -> dict[str, Any]:
    skill_path = _load_skill_path_map().get(skill_key)
    if skill_path is None or not skill_path.exists():
        raise FileNotFoundError(f"Skill file not found for skill_key={skill_key}")

    lines = skill_path.read_text(encoding="utf-8").splitlines()
    prefix = f"   - {field_label}（"
    target_line = ""
    options: list[str] = []
    for line in lines:
        if line.startswith(prefix) and line.endswith("）"):
            target_line = line
            options_str = line[len(prefix):-1]
            options = [item.strip() for item in options_str.split("/") if item.strip()]
            break
    if not target_line:
        raise ValueError(f"Field line not found: skill_key={skill_key}, field_label={field_label}")

    return {
        "skill_path": skill_path,
        "field_line": target_line,
        "options": options,
    }


def _filter_cases(rows: list[dict[str, Any]], skill_key: str, field_label: str) -> list[dict[str, Any]]:
    return [
        row for row in rows
        if str(row.get("skill_key", "")).strip() == skill_key
        and str(row.get("field_label", "")).strip() == field_label
    ]


def _consume_until(target_last_line: int, poll_seconds: float, timeout_seconds: float) -> int:
    consumer = FileQueueConsumer(poll_seconds=poll_seconds)
    deadline = time.time() + timeout_seconds

    while consumer._last_line < target_last_line:
        if time.time() > deadline:
            raise TimeoutError(
                f"Queue consume timeout. current_last_line={consumer._last_line}, target={target_last_line}"
            )
        pending = consumer._iter_unconsumed()
        if not pending:
            time.sleep(poll_seconds)
            continue

        for line_no, candidate in pending:
            _handle_candidate(candidate)
            consumer._last_line = line_no
            consumer._save_state_line(line_no)
            if consumer._last_line >= target_last_line:
                break

    return consumer._last_line


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "yes"}


def run() -> None:
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = PROJECT_ROOT / "benchmark" / "runs" / f"{timestamp}_minimal"
    run_dir.mkdir(parents=True, exist_ok=True)

    train_rows = _load_jsonl(args.train)
    test_rows = _load_jsonl(args.test)

    train_cases = _filter_cases(train_rows, args.skill_key, args.field_label)
    test_cases = _filter_cases(test_rows, args.skill_key, args.field_label)

    if not train_cases:
        raise ValueError("No matching train cases for the target skill/field.")
    if not test_cases:
        raise ValueError("No matching test cases for the target skill/field.")

    before = _get_field_snapshot(args.skill_key, args.field_label)
    before_options = before["options"]
    before_set = {_normalize_slot(option) for option in before_options}

    queue_before = _count_queue_lines()
    if args.reset_consumer_state:
        _set_consumer_state(queue_before)

    enqueued_count = 0
    for row in train_cases:
        candidate = _to_candidate(row)
        enqueue_candidate(candidate)
        enqueued_count += 1

    queue_target = queue_before + enqueued_count
    consumed_line = _consume_until(
        target_last_line=queue_target,
        poll_seconds=args.poll_seconds,
        timeout_seconds=args.consume_timeout_seconds,
    )

    after = _get_field_snapshot(args.skill_key, args.field_label)
    after_options = after["options"]
    after_set = {_normalize_slot(option) for option in after_options}

    positives = 0
    true_positive = 0
    recall_predictions: list[dict[str, Any]] = []
    for row in test_cases:
        gold_need_evolve = _safe_bool(row.get("gold_need_evolve"))
        if gold_need_evolve:
            positives += 1

        candidate = _to_candidate(row, source="benchmark_eval")
        should_evolve = False
        judge_reason = ""
        judge_error = ""
        try:
            judge = _judge_with_llm(candidate)
            should_evolve = bool(judge.should_evolve)
            judge_reason = judge.reason
        except Exception as exc:
            judge_error = str(exc)

        if gold_need_evolve and should_evolve:
            true_positive += 1

        recall_predictions.append({
            "case_id": row.get("case_id", ""),
            "gold_need_evolve": gold_need_evolve,
            "pred_should_evolve": should_evolve,
            "judge_reason": judge_reason,
            "judge_error": judge_error,
        })

    recall = (true_positive / positives) if positives else 0.0

    # ---------------------------------------------------------------------------
    # benchmark 1: slot coverage
    # ---------------------------------------------------------------------------
    gold_slots = [str(row.get("gold_slot", "")).strip() for row in test_cases if str(row.get("gold_slot", "")).strip()]
    
    total_occurrence = len(gold_slots)
    hits_before = sum(1 for slot in gold_slots if _normalize_slot(slot) in before_set)
    hits_after = sum(1 for slot in gold_slots if _normalize_slot(slot) in after_set)
    coverage_before = (hits_before / total_occurrence) if total_occurrence else 0.0
    coverage_after = (hits_after / total_occurrence) if total_occurrence else 0.0

    metrics = {
        "meta": {
            "timestamp": timestamp,
            "model_id": MODEL_ID,
            "skill_key": args.skill_key,
            "field_label": args.field_label,
            "train_path": str(args.train),
            "test_path": str(args.test),
            "train_sha256": _sha256(args.train),
            "test_sha256": _sha256(args.test),
            "reset_consumer_state": args.reset_consumer_state,
            "queue_before_lines": queue_before,
            "queue_target_line": queue_target,
            "consumer_last_line_after_run": consumed_line,
        },
        "need_evolve_recall": {
            "true_positive": true_positive,
            "positive_total": positives,
            "recall": recall,
        },
        "slot_coverage": {
            "denominator": "test_slot_occurrence",
            "total_occurrence": total_occurrence,
            "hits_before": hits_before,
            "hits_after": hits_after,
            "coverage_before": coverage_before,
            "coverage_after": coverage_after,
            "coverage_uplift_abs": coverage_after - coverage_before,
        },
        "pool_snapshot": {
            "before_options": before_options,
            "after_options": after_options,
        },
    }

    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    predictions_path = run_dir / "need_evolve_predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as f:
        for row in recall_predictions:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    before_after_path = run_dir / "before_after_skill_line.txt"
    before_after_path.write_text(
        f"[before]\n{before['field_line']}\n\n[after]\n{after['field_line']}\n",
        encoding="utf-8",
    )

    report_path = run_dir / "metrics_report.md"
    report_path.write_text(
        "\n".join([
            "# Minimal Benchmark Report",
            "",
            f"- timestamp: `{timestamp}`",
            f"- model: `{MODEL_ID}`",
            f"- target: `{args.skill_key} / {args.field_label}`",
            "",
            "## Need-Evolve Recall",
            f"- true_positive: `{true_positive}`",
            f"- positive_total: `{positives}`",
            f"- recall: `{recall:.4f}`",
            "",
            "## Slot Coverage",
            "- denominator: `test_slot_occurrence`",
            f"- total_occurrence: `{total_occurrence}`",
            f"- hits_before: `{hits_before}`",
            f"- hits_after: `{hits_after}`",
            f"- coverage_before: `{coverage_before:.4f}`",
            f"- coverage_after: `{coverage_after:.4f}`",
            f"- coverage_uplift_abs: `{(coverage_after - coverage_before):.4f}`",
            "",
            "## Skill Option Snapshot",
            f"- before: `{ '/'.join(before_options) }`",
            f"- after: `{ '/'.join(after_options) }`",
            "",
            "## Artifact Files",
            f"- metrics: `{metrics_path}`",
            f"- predictions: `{predictions_path}`",
            f"- before_after: `{before_after_path}`",
        ]) + "\n",
        encoding="utf-8",
    )

    print(f"[benchmark] done. run_dir={run_dir}")
    print(f"[benchmark] metrics={metrics_path}")
    print(f"[benchmark] report={report_path}")


if __name__ == "__main__":
    run()
