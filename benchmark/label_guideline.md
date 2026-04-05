# Label Guideline for `eval_cases.csv`

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
