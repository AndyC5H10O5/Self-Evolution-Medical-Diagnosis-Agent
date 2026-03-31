---
name: sore-throat
description: A pre-consultation workflow for sore throat to distinguish common infections and potential airway risks.
---

# 喉咙痛问诊流程 Skill

你当前进入“喉咙痛”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认吞咽痛程度、病程与是否单侧加重。
2. 追问伴随症状：发热、咳嗽、流鼻涕、声音嘶哑、扁桃体肿痛。
3. 追问风险：近期感冒接触史、过度用嗓、吸烟饮酒。
4. 红旗：呼吸困难、流口水无法吞咽、高热持续，建议急诊或耳鼻喉就诊。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
