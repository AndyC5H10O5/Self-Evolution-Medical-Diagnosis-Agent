---
name: fatigue
description: A pre-consultation workflow for fatigue covering duration, severity, sleep and mood factors, and systemic red flags.
---

# 疲劳问诊流程 Skill

你当前进入“疲劳”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认疲劳持续时间、严重程度及是否影响日常功能。
2. 追问生活因素：睡眠质量、压力、饮食、运动、工作负荷。
3. 追问伴随症状：发热、体重变化、心悸、气短、情绪低落。
4. 红旗：进行性加重、明显消瘦、胸闷气短或持续低热，建议线下系统评估。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
