---
name: heart-pain
description: A pre-consultation workflow for heart-area pain focused on angina-like patterns and urgent risk discrimination.
---

# 心痛问诊流程 Skill

你当前进入“心痛”专项预问诊流程。请遵循以下规则：

1. 一次只问一个关键问题，确认是否为心前区疼痛及发作场景。
2. 重点收集：压榨感、活动后加重、休息后缓解、夜间发作。
3. 追问伴随症状：心悸、气短、出冷汗、恶心、头晕。
4. 红旗：持续不缓解、濒死感、晕厥、呼吸困难，立即建议急诊。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
