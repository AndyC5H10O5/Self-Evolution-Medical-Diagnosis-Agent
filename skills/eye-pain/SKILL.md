---
name: eye-pain
description: A pre-consultation workflow for eye pain including visual symptoms, trauma history, and ophthalmic red-flag triage.
---

# 眼痛问诊流程 Skill

你当前进入“眼痛”专项预问诊流程。请遵循以下规则：

1. 一次一问，优先确认单眼/双眼、疼痛程度与持续时间。
2. 重点收集：畏光、流泪、视力下降、眼红、分泌物、异物感。
3. 追问风险史：隐形眼镜佩戴、外伤、化学刺激、长时间用眼。
4. 红旗：突发视力明显下降、剧烈眼痛伴头痛呕吐、外伤后视物异常，建议急诊眼科。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
