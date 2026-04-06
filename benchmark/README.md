# Benchmark

本目录提供两套脚本：

- `run_minimal_benchmark.py`：单症状单字段最小闭环
- `run_benchmark.py`：多症状多字段通用评测（推荐）

两者都验证以下两项指标：

- `Need-Evolve Recall`
- `Slot Coverage`（分母 = 测试集 `gold_slot` 出现总次数）

流程均不经过问诊器 REPL，而是直接构造“模拟问诊器上报”的候选，写入进化队列并由进化器消费，随后观测 `skills` 实际进化。

## 目录

- `benchmark/cases/minimal_train.jsonl`：最小训练样例（单组）
- `benchmark/cases/minimal_test.jsonl`：最小测试样例（单组）
- `benchmark/cases/train_v1.jsonl`：混合训练样例（`headache`/`vomiting`/`insomnia`）
- `benchmark/cases/test_v1.jsonl`：混合测试样例（`headache`/`vomiting`/`insomnia`）
- `benchmark/run_minimal_benchmark.py`：最小闭环脚本
- `benchmark/run_benchmark.py`：通用脚本
- `benchmark/runs/<timestamp>_minimal/` 与 `benchmark/runs/<timestamp>_benchmark/`：运行产物

## Case Schema（V1）

每条 JSONL case 字段如下：

- `case_id`：样本 ID
- `skill_key`：症状 skill（示例：`headache`）
- `field_label`：字段名（示例：`头痛性质`）
- `user_turn`：患者原话
- `candidate_option`：候选选项短语（2-12 字，避免 `/` 和括号）
- `last_assistant_question_field`：上一问字段（通常与 `field_label` 一致）
- `gold_need_evolve`：是否应进化（用于 Recall）
- `gold_slot`：该样本用于覆盖率统计的目标 slot

## Case Schema（通用）

每条 JSONL case 字段如下：

- `case_id`：样本 ID
- `skill_key`：症状 skill（如 `headache`）
- `field_label`：字段名（如 `头痛性质`、`呕吐性质`、`睡眠问题类型`）
- `user_turn`：患者原话
- `candidate_option`：候选选项短语（2-12 字，避免 `/` 和括号）
- `last_assistant_question_field`：上一问字段（通常与 `field_label` 一致）
- `gold_need_evolve`：是否应进化（用于 Recall）
- `gold_slot`：该样本用于覆盖率统计的目标 slot

## 运行（最小闭环）

在项目根目录执行：

```bash
python benchmark/run_minimal_benchmark.py
```

可选参数：

```bash
python benchmark/run_minimal_benchmark.py \
  --skill-key headache \
  --field-label 头痛性质 \
  --train benchmark/cases/minimal_train.jsonl \
  --test benchmark/cases/minimal_test.jsonl \
  --consume-timeout-seconds 120 \
  --poll-seconds 0.5
```

默认会重置消费游标到“当前队列末尾”，仅消费本次新增训练样本。若要关闭该行为：

```bash
python benchmark/run_minimal_benchmark.py --no-reset-consumer-state
```

## 运行（通用脚本）

在项目根目录执行：

```bash
python benchmark/run_benchmark.py
```

可选参数：

```bash
python benchmark/run_benchmark.py \
  --train benchmark/cases/train_v1.jsonl \
  --test benchmark/cases/test_v1.jsonl \
  --skills headache,vomiting,insomnia \
  --consume-timeout-seconds 180 \
  --poll-seconds 0.5
```

默认会重置消费游标到“当前队列末尾”，仅消费本次新增训练样本。若要关闭该行为：

```bash
python benchmark/run_benchmark.py --no-reset-consumer-state
```

## 指标定义

### Need-Evolve Recall

- `P`: 测试集中 `gold_need_evolve=true` 的样本数
- `TP`: 上述样本中，进化器判定 `should_evolve=true` 的样本数
- `Recall = TP / P`

### Slot Coverage（occurrence）

- 分母：测试集 `gold_slot` 出现总次数（occurrence）
- 分子：`gold_slot` 在字段选项池中的命中次数
- 输出 `coverage_before`、`coverage_after` 与 `coverage_uplift_abs`

## 运行产物

每次运行会生成：

- `metrics.json`：核心指标与元信息
- `metrics_report.md`：可读报告
- `need_evolve_predictions.jsonl`：Recall 样本级判定明细
- `before_after_skill_line.txt`：字段进化前后对比（通用脚本中为多分组）

## 验收要点

1. 运行后可在 `skills/<skill>/SKILL.md` 看到对应字段选项变化（若判定通过）。
2. `metrics.json` 包含全局指标与 `by_group["skill::field"]` 分组指标。
3. `before_after_skill_line.txt` 可直接确认各分组“进化前后”字段行差异。
