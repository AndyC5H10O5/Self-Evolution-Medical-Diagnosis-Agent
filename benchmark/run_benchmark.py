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
from agent_core.skill_router import get_evolvable_fields
from evolve_core.main import _handle_candidate, _judge_with_llm
from evolve_core.schemas import EvolutionCandidate
from evolve_core.worker import FileQueueConsumer, QUEUE_FILE, STATE_FILE, enqueue_candidate
from tools.skill_evolve_tool import _load_skill_path_map


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run generic benchmark for evolver.")
    parser.add_argument(
        "--train",
        type=Path,
        default=PROJECT_ROOT / "benchmark" / "cases" / "train_v1.jsonl",
        help="Train jsonl path.",
    )
    parser.add_argument(
        "--test",
        type=Path,
        default=PROJECT_ROOT / "benchmark" / "cases" / "test_v1.jsonl",
        help="Test jsonl path.",
    )
    parser.add_argument(
        "--skills",
        type=str,
        default="",
        help="Optional comma separated skill keys to include, e.g. headache,vomiting,insomnia",
    )
    parser.add_argument(
        "--consume-timeout-seconds",
        type=float,
        default=180.0,
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


def _safe_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in {"1", "true", "yes"}


def _normalize_slot(text: str) -> str:
    value = (text or "").strip().replace(" ", "").replace("\u3000", "")
    value = value.replace("，", ",").replace("；", ";").replace("：", ":")
    return value


def _to_candidate(raw: dict[str, Any], source: str = "benchmark") -> EvolutionCandidate:
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


def _group_key(skill_key: str, field_label: str) -> str:
    return f"{skill_key}::{field_label}"


def _parse_group_key(group: str) -> tuple[str, str]:
    skill_key, field_label = group.split("::", 1)
    return skill_key, field_label


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


def _init_group_metric() -> dict[str, Any]:
    return {
        "need_evolve_recall": {
            "true_positive": 0,
            "positive_total": 0,
            "recall": 0.0,
        },
        "slot_coverage": {
            "denominator": "test_slot_occurrence",
            "total_occurrence": 0,
            "hits_before": 0,
            "hits_after": 0,
            "coverage_before": 0.0,
            "coverage_after": 0.0,
            "coverage_uplift_abs": 0.0,
        },
        "pool_snapshot": {
            "before_options": [],
            "after_options": [],
        },
    }


def _apply_skill_filter(rows: list[dict[str, Any]], skill_filter: set[str]) -> list[dict[str, Any]]:
    if not skill_filter:
        return rows
    return [row for row in rows if str(row.get("skill_key", "")).strip() in skill_filter]


def run() -> None:
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = PROJECT_ROOT / "benchmark" / "runs" / f"{timestamp}_benchmark"
    run_dir.mkdir(parents=True, exist_ok=True)

    skill_filter = {item.strip() for item in args.skills.split(",") if item.strip()}

    train_rows = _apply_skill_filter(_load_jsonl(args.train), skill_filter)
    test_rows = _apply_skill_filter(_load_jsonl(args.test), skill_filter)
    if not train_rows:
        raise ValueError("No train cases after skill filtering.")
    if not test_rows:
        raise ValueError("No test cases after skill filtering.")

    groups = sorted({
        _group_key(str(row.get("skill_key", "")).strip(), str(row.get("field_label", "")).strip())
        for row in (train_rows + test_rows)
        if str(row.get("skill_key", "")).strip() and str(row.get("field_label", "")).strip()
    })
    if not groups:
        raise ValueError("No valid (skill_key, field_label) groups found.")

    snapshots_before: dict[str, dict[str, Any]] = {}
    for group in groups:
        skill_key, field_label = _parse_group_key(group)
        snapshots_before[group] = _get_field_snapshot(skill_key, field_label)

    queue_before = _count_queue_lines()
    if args.reset_consumer_state:
        _set_consumer_state(queue_before)

    enqueued_count = 0
    for row in train_rows:
        enqueue_candidate(_to_candidate(row, source="benchmark_train"))
        enqueued_count += 1

    queue_target = queue_before + enqueued_count
    consumed_line = _consume_until(
        target_last_line=queue_target,
        poll_seconds=args.poll_seconds,
        timeout_seconds=args.consume_timeout_seconds,
    )

    snapshots_after: dict[str, dict[str, Any]] = {}
    for group in groups:
        skill_key, field_label = _parse_group_key(group)
        snapshots_after[group] = _get_field_snapshot(skill_key, field_label)

    group_metrics: dict[str, dict[str, Any]] = {group: _init_group_metric() for group in groups}
    predictions: list[dict[str, Any]] = []

    global_positive = 0
    global_tp = 0
    global_occurrence = 0
    global_hits_before = 0
    global_hits_after = 0

    before_sets = {
        group: {_normalize_slot(option) for option in snapshots_before[group]["options"]}
        for group in groups
    }
    after_sets = {
        group: {_normalize_slot(option) for option in snapshots_after[group]["options"]}
        for group in groups
    }

    for row in test_rows:
        skill_key = str(row.get("skill_key", "")).strip()
        field_label = str(row.get("field_label", "")).strip()
        group = _group_key(skill_key, field_label)
        if group not in group_metrics:
            continue

        evolvable_fields = set(get_evolvable_fields(skill_key))
        is_evolvable_field = field_label in evolvable_fields

        gold_need_evolve = _safe_bool(row.get("gold_need_evolve"))
        should_evolve = False
        judge_reason = ""
        judge_error = ""

        if gold_need_evolve:
            group_metrics[group]["need_evolve_recall"]["positive_total"] += 1
            global_positive += 1

        candidate = _to_candidate(row, source="benchmark_eval")
        try:
            judge = _judge_with_llm(candidate)
            should_evolve = bool(judge.should_evolve)
            judge_reason = judge.reason
        except Exception as exc:
            judge_error = str(exc)

        if gold_need_evolve and should_evolve:
            group_metrics[group]["need_evolve_recall"]["true_positive"] += 1
            global_tp += 1

        gold_slot = str(row.get("gold_slot", "")).strip()
        # Coverage only counts evolvable fields.
        if gold_slot and is_evolvable_field:
            slot = _normalize_slot(gold_slot)
            group_metrics[group]["slot_coverage"]["total_occurrence"] += 1
            global_occurrence += 1
            if slot in before_sets[group]:
                group_metrics[group]["slot_coverage"]["hits_before"] += 1
                global_hits_before += 1
            if slot in after_sets[group]:
                group_metrics[group]["slot_coverage"]["hits_after"] += 1
                global_hits_after += 1

        predictions.append({
            "case_id": row.get("case_id", ""),
            "group": group,
            "skill_key": skill_key,
            "field_label": field_label,
            "gold_need_evolve": gold_need_evolve,
            "pred_should_evolve": should_evolve,
            "judge_reason": judge_reason,
            "judge_error": judge_error,
            "gold_slot": gold_slot,
        })

    for group in groups:
        recall_data = group_metrics[group]["need_evolve_recall"]
        positives = recall_data["positive_total"]
        recall_data["recall"] = (recall_data["true_positive"] / positives) if positives else 0.0

        coverage_data = group_metrics[group]["slot_coverage"]
        total_occurrence = coverage_data["total_occurrence"]
        coverage_data["coverage_before"] = (
            coverage_data["hits_before"] / total_occurrence if total_occurrence else 0.0
        )
        coverage_data["coverage_after"] = (
            coverage_data["hits_after"] / total_occurrence if total_occurrence else 0.0
        )
        coverage_data["coverage_uplift_abs"] = coverage_data["coverage_after"] - coverage_data["coverage_before"]

        group_metrics[group]["pool_snapshot"] = {
            "before_options": snapshots_before[group]["options"],
            "after_options": snapshots_after[group]["options"],
        }

    global_recall = (global_tp / global_positive) if global_positive else 0.0
    global_coverage_before = (global_hits_before / global_occurrence) if global_occurrence else 0.0
    global_coverage_after = (global_hits_after / global_occurrence) if global_occurrence else 0.0

    metrics = {
        "meta": {
            "timestamp": timestamp,
            "model_id": MODEL_ID,
            "train_path": str(args.train),
            "test_path": str(args.test),
            "train_sha256": _sha256(args.train),
            "test_sha256": _sha256(args.test),
            "skills_filter": sorted(skill_filter),
            "groups": groups,
            "reset_consumer_state": args.reset_consumer_state,
            "queue_before_lines": queue_before,
            "queue_target_line": queue_target,
            "consumer_last_line_after_run": consumed_line,
        },
        "global": {
            "need_evolve_recall": {
                "true_positive": global_tp,
                "positive_total": global_positive,
                "recall": global_recall,
            },
            "slot_coverage": {
                "denominator": "test_slot_occurrence_evolvable_only",
                "total_occurrence": global_occurrence,
                "hits_before": global_hits_before,
                "hits_after": global_hits_after,
                "coverage_before": global_coverage_before,
                "coverage_after": global_coverage_after,
                "coverage_uplift_abs": global_coverage_after - global_coverage_before,
            },
        },
        "by_group": group_metrics,
    }

    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    predictions_path = run_dir / "need_evolve_predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as f:
        for row in predictions:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    before_after_path = run_dir / "before_after_skill_line.txt"
    blocks: list[str] = []
    for group in groups:
        skill_key, field_label = _parse_group_key(group)
        before_line = snapshots_before[group]["field_line"]
        after_line = snapshots_after[group]["field_line"]
        blocks.append(
            "\n".join([
                f"[group] {group}",
                f"[skill_path] {snapshots_before[group]['skill_path']}",
                "[before]",
                before_line,
                "[after]",
                after_line,
                "",
            ])
        )
    before_after_path.write_text("\n".join(blocks), encoding="utf-8")

    report_path = run_dir / "metrics_report.md"
    lines = [
        "# Benchmark Report",
        "",
        f"- timestamp: `{timestamp}`",
        f"- model: `{MODEL_ID}`",
        f"- groups: `{len(groups)}`",
        f"- skills_filter: `{','.join(sorted(skill_filter)) if skill_filter else 'all'}`",
        "",
        "## Global",
        f"- need_evolve_recall: `{global_recall:.4f}` ({global_tp}/{global_positive})",
        (
            f"- slot_coverage_before: `{global_coverage_before:.4f}` "
            f"({global_hits_before}/{global_occurrence})"
        ),
        (
            f"- slot_coverage_after: `{global_coverage_after:.4f}` "
            f"({global_hits_after}/{global_occurrence})"
        ),
        f"- slot_coverage_uplift_abs: `{(global_coverage_after - global_coverage_before):.4f}`",
        "",
        "## By Group",
    ]
    for group in groups:
        gm = group_metrics[group]
        recall_data = gm["need_evolve_recall"]
        coverage_data = gm["slot_coverage"]
        lines.extend([
            f"### {group}",
            (
                f"- need_evolve_recall: `{recall_data['recall']:.4f}` "
                f"({recall_data['true_positive']}/{recall_data['positive_total']})"
            ),
            (
                f"- slot_coverage_before: `{coverage_data['coverage_before']:.4f}` "
                f"({coverage_data['hits_before']}/{coverage_data['total_occurrence']})"
            ),
            (
                f"- slot_coverage_after: `{coverage_data['coverage_after']:.4f}` "
                f"({coverage_data['hits_after']}/{coverage_data['total_occurrence']})"
            ),
            f"- slot_coverage_uplift_abs: `{coverage_data['coverage_uplift_abs']:.4f}`",
            f"- before_options: `{ '/'.join(gm['pool_snapshot']['before_options']) }`",
            f"- after_options: `{ '/'.join(gm['pool_snapshot']['after_options']) }`",
            "",
        ])

    lines.extend([
        "## Artifact Files",
        f"- metrics: `{metrics_path}`",
        f"- predictions: `{predictions_path}`",
        f"- before_after: `{before_after_path}`",
    ])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[benchmark] done. run_dir={run_dir}")
    print(f"[benchmark] metrics={metrics_path}")
    print(f"[benchmark] report={report_path}")


if __name__ == "__main__":
    run()
