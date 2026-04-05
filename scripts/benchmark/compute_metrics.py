from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def compute(rows: list[dict]) -> dict[str, float]:
    total = len(rows)
    tp = fp = fn = tn = 0
    should_total = 0
    correct_field = 0
    called = 0

    for r in rows:
        g = bool((r.get("gold") or {}).get("should_evolve"))
        p = bool((r.get("prediction") or {}).get("should_evolve"))
        if g:
            should_total += 1
        if p:
            called += 1

        if g and p:
            tp += 1
            gf = str((r.get("gold") or {}).get("field_label") or "").strip()
            pf = str((r.get("prediction") or {}).get("field_label") or "").strip()
            if gf and pf and gf == pf:
                correct_field += 1
        elif (not g) and p:
            fp += 1
        elif g and (not p):
            fn += 1
        else:
            tn += 1

    metrics = {
        "total_samples": float(total),
        "tp": float(tp),
        "fp": float(fp),
        "fn": float(fn),
        "tn": float(tn),
        "evolve_precision": _safe_div(tp, tp + fp),
        "false_evolve_rate": _safe_div(fp, total),
        "missed_evolve_rate": _safe_div(fn, should_total),
        "trigger_accuracy": _safe_div(tp + tn, total),
        "field_match_rate_when_called": _safe_div(correct_field, called),
    }
    return metrics


def write_csv(metrics: dict[str, float], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for k, v in metrics.items():
            writer.writerow([k, v])


def write_markdown(metrics: dict[str, float], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Benchmark Metrics Report",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for k, v in metrics.items():
        lines.append(f"| {k} | {v:.6f} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute benchmark metrics from JSONL results.")
    parser.add_argument("--input", required=True, help="Path to raw_results.jsonl")
    parser.add_argument("--csv-out", default="benchmark/metrics.csv")
    parser.add_argument("--md-out", default="benchmark/metrics_report.md")
    args = parser.parse_args()

    rows = _load_jsonl(Path(args.input))
    metrics = compute(rows)
    write_csv(metrics, Path(args.csv_out))
    write_markdown(metrics, Path(args.md_out))
    print(f"Wrote metrics csv to: {args.csv_out}")
    print(f"Wrote metrics report to: {args.md_out}")


if __name__ == "__main__":
    main()
