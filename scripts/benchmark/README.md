# Benchmark Scripts

## Quick Start

1. 审计公开数据集：

```bash
python scripts/benchmark/audit_dataset.py --output benchmark/audit_summary.json
```

2. 生成评测样本模板：

```bash
python scripts/benchmark/build_evalset.py --cases-out benchmark/eval_cases.csv --guideline-out benchmark/label_guideline.md
```

3. 运行 baseline：

```bash
python scripts/benchmark/run_benchmark.py --mode baseline --cases benchmark/eval_cases.csv --output benchmark/runs/baseline/raw_results.jsonl
```

4. 运行 evolve（需 API Key）：

```bash
python scripts/benchmark/run_benchmark.py --mode evolve --cases benchmark/eval_cases.csv --output benchmark/runs/evolve/raw_results.jsonl
```

5. 计算指标：

```bash
python scripts/benchmark/compute_metrics.py --input benchmark/runs/evolve/raw_results.jsonl --csv-out benchmark/runs/evolve/metrics.csv --md-out benchmark/runs/evolve/metrics_report.md
```

6. 可选画图：

```bash
python scripts/benchmark/plot_metrics.py --csv benchmark/runs/evolve/metrics.csv --out benchmark/runs/evolve/metrics.png
```
