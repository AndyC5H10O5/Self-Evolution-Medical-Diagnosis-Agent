---
name: waist-pain
description: A pre-consultation workflow for waist pain focused on mechanical causes, nerve involvement, and red-flag screening.
---

# 腰痛问诊流程 Skill

你当前进入“腰痛”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认疼痛位置、持续时间、活动相关性。
2. 追问放射痛：是否向臀部或下肢放射，是否麻木无力。
3. 追问诱因：久坐、搬重物、扭伤、受凉。
4. 红旗：大小便异常、进行性下肢无力、发热伴腰痛、外伤后剧痛，建议急诊或骨科就诊。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
