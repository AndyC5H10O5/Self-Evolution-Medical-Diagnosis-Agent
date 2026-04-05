from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_HEADERS = [
    "sample_id",
    "split",
    "skill_key",
    "last_assistant_question_field",
    "user_turn",
    "should_evolve_gold",
    "gold_field_label",
    "gold_new_option",
    "is_existing_option_or_synonym",
    "notes",
]


SEED_ROWS = [
    {
        "sample_id": "S0001",
        "split": "test",
        "skill_key": "headache",
        "last_assistant_question_field": "头痛性质",
        "user_turn": "像一跳一跳地疼",
        "should_evolve_gold": "0",
        "gold_field_label": "头痛性质",
        "gold_new_option": "搏动样",
        "is_existing_option_or_synonym": "1",
        "notes": "已有选项同义，不应进化",
    },
    {
        "sample_id": "S0002",
        "split": "test",
        "skill_key": "eye_pain",
        "last_assistant_question_field": "疼痛性质",
        "user_turn": "触痛",
        "should_evolve_gold": "1",
        "gold_field_label": "疼痛性质",
        "gold_new_option": "触痛",
        "is_existing_option_or_synonym": "0",
        "notes": "可进化新选项",
    },
    {
        "sample_id": "S0003",
        "split": "test",
        "skill_key": "eye_pain",
        "last_assistant_question_field": "疼痛部位",
        "user_turn": "A",
        "should_evolve_gold": "0",
        "gold_field_label": "",
        "gold_new_option": "",
        "is_existing_option_or_synonym": "1",
        "notes": "字母选项，禁止进化",
    },
]


def write_eval_cases(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DEFAULT_HEADERS)
        writer.writeheader()
        writer.writerows(SEED_ROWS)


def write_guideline(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = """# Label Guideline for `eval_cases.csv`

## 1. 字段说明
- `should_evolve_gold`：该轮是否应该触发 `skill_evolve`（1/0）
- `gold_field_label`：若应进化，目标字段
- `gold_new_option`：若应进化，标准新选项
- `is_existing_option_or_synonym`：用户回答是否是已有选项或其明显同义表达（1/0）

## 2. 标注规则（核心）
1. 如果用户回答是字母选项（A/B/C...）或对已有选项复述，同义表达视为不应进化。
2. 只有当用户提供了可沉淀为“短标签”的新表达，并且字段明确时，标注应进化。
3. 无法唯一匹配字段时，默认 `should_evolve_gold=0`。

## 3. 质量控制
- 至少两人交叉标注10%样本，分歧样本集中复核。
- 对每个 skill 保证正负样本都出现，避免分布偏置。
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build benchmark eval set template.")
    parser.add_argument("--cases-out", default="benchmark/eval_cases.csv")
    parser.add_argument("--guideline-out", default="benchmark/label_guideline.md")
    args = parser.parse_args()

    write_eval_cases(Path(args.cases_out))
    write_guideline(Path(args.guideline_out))
    print(f"Wrote eval cases to: {args.cases_out}")
    print(f"Wrote label guideline to: {args.guideline_out}")


if __name__ == "__main__":
    main()
