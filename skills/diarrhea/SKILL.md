---
name: diarrhea
description: A pre-consultation workflow for diarrhea focused on frequency, stool characteristics, dehydration signs, and infection risks.
---

# 腹泻问诊流程 Skill

你当前进入“腹泻”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认腹泻次数、持续时间与粪便性状。
2. 追问伴随症状：腹痛、发热、恶心呕吐、里急后重、便血。
3. 评估脱水：口干、尿少、乏力、头晕。
4. 红旗：便血、高热持续、明显脱水、剧烈腹痛，建议及时线下就医。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
