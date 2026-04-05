from __future__ import annotations

import argparse
import csv
from pathlib import Path


def load_metrics(path: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                out[row["metric"]] = float(row["value"])
            except Exception:
                continue
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot benchmark metrics (requires matplotlib).")
    parser.add_argument("--csv", default="benchmark/metrics.csv")
    parser.add_argument("--out", default="benchmark/metrics.png")
    args = parser.parse_args()

    metrics = load_metrics(Path(args.csv))
    keys = [
        "evolve_precision",
        "false_evolve_rate",
        "missed_evolve_rate",
        "trigger_accuracy",
        "field_match_rate_when_called",
    ]
    vals = [metrics.get(k, 0.0) for k in keys]

    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"matplotlib not installed: {exc}")

    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111)
    ax.bar(keys, vals)
    ax.set_ylim(0, 1.0)
    ax.set_title("Benchmark Key Metrics")
    ax.set_ylabel("Score")
    plt.xticks(rotation=20, ha="right")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(args.out, dpi=160)
    print(f"Plot saved to: {args.out}")


if __name__ == "__main__":
    main()
