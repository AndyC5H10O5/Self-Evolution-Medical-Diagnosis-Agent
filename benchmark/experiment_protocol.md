# Experiment Protocol (Baseline vs Evolve)

## 1. 目标

用同一批样本比较两种策略：

- `baseline`：不触发进化（固定返回 should_evolve=false）
- `evolve`：由模型判别是否进化

## 2. 控制变量

保持一致：

- 同一 `eval_cases.csv`
- 同一模型（`--model`）
- 同一温度（建议 `--temperature 0`）
- 同一API入口（`--base-url`）

## 3. 运行步骤

### Step A: 生成 baseline 结果

```bash
python scripts/benchmark/run_benchmark.py --mode baseline --cases benchmark/eval_cases.csv --output benchmark/runs/baseline/raw_results.jsonl
```

### Step B: 生成 evolve 结果

```bash
python scripts/benchmark/run_benchmark.py --mode evolve --cases benchmark/eval_cases.csv --output benchmark/runs/evolve/raw_results.jsonl
```

### Step C: 分别计算指标

```bash
python scripts/benchmark/compute_metrics.py --input benchmark/runs/baseline/raw_results.jsonl --csv-out benchmark/runs/baseline/metrics.csv --md-out benchmark/runs/baseline/metrics_report.md
python scripts/benchmark/compute_metrics.py --input benchmark/runs/evolve/raw_results.jsonl --csv-out benchmark/runs/evolve/metrics.csv --md-out benchmark/runs/evolve/metrics_report.md
```

## 4. 核心指标解释

- `evolve_precision`：触发进化中有多少是正确触发
- `false_evolve_rate`：不该进化却触发的比例
- `missed_evolve_rate`：应进化却没触发的比例
- `trigger_accuracy`：对 should_evolve 的整体判定正确率
- `field_match_rate_when_called`：触发后字段匹配准确率

## 5. 报告输出

论文建议至少展示：

1. Baseline vs Evolve 指标对照表
2. 三类典型错误样例（误触发、漏触发、字段错位）
3. 结论段：是否显著改善、代价是什么、下一步优化点
