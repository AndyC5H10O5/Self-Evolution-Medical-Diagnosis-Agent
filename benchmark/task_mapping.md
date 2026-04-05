# Task Mapping: Benchmark -> Medical Pre-consultation Evolution

## 1. 研究任务分解

本项目评测拆为两层：

- **T1 过程层（触发正确性）**
  - 目标：判断模型是否在正确时机触发 `skill_evolve`
  - 关键问题：不该触发时是否能克制、该触发时是否能命中

- **T2 结果层（业务效果）**
  - 目标：验证启用进化后，问诊采集质量是否提高
  - 关键问题：引导选项覆盖率、字段完整率是否提升

## 2. 字段映射规范

| Benchmark概念 | 本项目字段 | 说明 |
|---|---|---|
| query / user turn | `user_turn` | 本轮用户输入文本 |
| scenario / skill | `skill_key` | 症状skill标识，如 `headache` |
| target slot | `last_assistant_question_field` | 上一轮助手询问维度 |
| evolve decision | `should_evolve_gold` | 金标：该轮是否应进化 |
| target update field | `gold_field_label` | 若应进化，目标字段 |
| target option | `gold_new_option` | 若应进化，新增选项 |
| duplicate/synonym | `is_existing_option_or_synonym` | 是否已有项或同义项 |

## 3. 判定口径（用于标注一致性）

1. 用户仅回复 A/B/C 或“选A”等，`should_evolve_gold=0`。
2. 用户表达属于已有选项或明显同义表达，`should_evolve_gold=0`。
3. 用户表达为可沉淀短标签（2-12字）且字段明确，`should_evolve_gold=1`。
4. 字段无法唯一确定时，默认 `should_evolve_gold=0`（保守原则）。

## 4. 与 obaydata 数据集的关系

- 该数据集主要用于借鉴评测组织方式（query + rubric + baseline/evolve 对照）。
- 本项目主结果使用 `eval_cases.csv`（与你项目字段强对齐）计算，不直接使用 obaydata 原始分数。
