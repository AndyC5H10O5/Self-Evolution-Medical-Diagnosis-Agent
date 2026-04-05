from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx


HF_DATASET_API = "https://huggingface.co/api/datasets/{dataset_id}"


def _classify_reusability(path: str) -> str:
    lower = path.lower()
    if lower.endswith(("rubric.json", "评分表.xlsx")):
        return "direct_reuse"
    if lower.endswith(("query.txt", "输入案例-潜在受试者信息.xlsx", "输入案例-研究项目受试标准.xlsx")):
        return "adapt_with_mapping"
    if "/skills/医疗/" in lower or "/data/skills/医疗/" in lower:
        return "adapt_with_mapping"
    return "not_recommended"


def audit_dataset(dataset_id: str) -> dict[str, Any]:
    url = HF_DATASET_API.format(dataset_id=dataset_id)
    resp = httpx.get(url, timeout=30.0)
    resp.raise_for_status()
    payload = resp.json()

    siblings = payload.get("siblings") or []
    files = [str(item.get("rfilename", "")).strip() for item in siblings if item.get("rfilename")]

    medical_files = [f for f in files if "医疗" in f or "clinical-trial-screening" in f]
    rubric_files = [f for f in files if f.lower().endswith("rubric.json") or f.endswith("评分表.xlsx")]
    query_like_files = [
        f
        for f in files
        if f.lower().endswith("query.txt") or "输入案例" in f or "案例" in f
    ]

    reusable = {"direct_reuse": [], "adapt_with_mapping": [], "not_recommended": []}
    for f in files:
        reusable[_classify_reusability(f)].append(f)

    summary = {
        "dataset_id": dataset_id,
        "last_modified": payload.get("lastModified"),
        "license": (payload.get("cardData") or {}).get("license"),
        "tags": payload.get("tags", []),
        "high_level_judgement": (
            "该数据集更适合作为评测方法模板（rubric/有无skill对照），"
            "不建议直接作为你项目主结果的唯一benchmark。"
        ),
        "counts": {
            "total_files": len(files),
            "medical_files": len(medical_files),
            "rubric_files": len(rubric_files),
            "query_like_files": len(query_like_files),
        },
        "important_paths": {
            "medical_subset_examples": medical_files[:20],
            "rubric_examples": rubric_files[:20],
            "query_examples": query_like_files[:20],
        },
        "reusability": reusable,
        "next_actions": [
            "复用rubric与对照评测范式（Baseline vs Evolve）。",
            "将query/案例映射为你项目字段（skill_key、should_evolve_gold）。",
            "构建你自己的医疗问诊gold set用于主实验结论。",
        ],
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Hugging Face benchmark dataset structure.")
    parser.add_argument(
        "--dataset-id",
        default="obaydata/claude-agent-skills-benchmark",
        help="Hugging Face dataset ID.",
    )
    parser.add_argument(
        "--output",
        default="benchmark/audit_summary.json",
        help="Output JSON path.",
    )
    args = parser.parse_args()

    summary = audit_dataset(args.dataset_id)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Audit summary written to: {output_path}")


if __name__ == "__main__":
    main()
