---
name: chest-pain
description: A pre-consultation workflow for chest pain emphasizing high-risk cardiovascular and pulmonary triage.
---

# 胸痛问诊流程 Skill

你当前进入“胸痛”专项预问诊流程。请遵循以下规则：

1. 一次一问，优先确认部位、性质（压榨/刺痛/闷痛）、持续时间与诱因。
2. 追问伴随症状：气短、出汗、恶心、放射痛（肩背/左臂/下颌）。
3. 追问风险因素：高血压、糖尿病、吸烟、心血管病史。
4. 红旗：持续胸痛>15分钟、呼吸困难、濒死感、晕厥，立即建议急诊。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
