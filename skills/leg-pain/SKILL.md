---
name: leg-pain
description: A pre-consultation workflow for leg pain including trauma, vascular risk, and neurological symptom screening.
---

# 腿痛问诊流程 Skill

你当前进入“腿痛”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认单侧/双侧、位置（大腿/小腿/膝周）与疼痛程度。
2. 追问诱因：运动拉伤、久站久走、外伤、受凉。
3. 追问伴随症状：肿胀、发热、麻木、无力、皮肤颜色改变。
4. 红旗：突发单侧肿痛伴呼吸不适、外伤后无法站立，建议急诊评估。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
