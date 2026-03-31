---
name: cough
description: A pre-consultation workflow for cough including duration, sputum pattern, and lower respiratory red flags.
---

# 咳嗽问诊流程 Skill

你当前进入“咳嗽”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认急性/慢性咳嗽及昼夜规律。
2. 收集痰液特征：无痰/白痰/黄痰/血痰，是否伴胸闷气促。
3. 追问伴随症状：发热、咽痛、流涕、喘息、胸痛。
4. 红旗：咯血、呼吸困难、高热不退、胸痛明显，建议尽快就医。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
