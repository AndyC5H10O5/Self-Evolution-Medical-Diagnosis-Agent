---
name: acne
description: A pre-consultation workflow for acne focusing on lesion pattern, triggers, skincare habits, and severity grading.
---

# 痤疮问诊流程 Skill

你当前进入“痤疮”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认部位（面部/背部/胸部）、病程和反复情况。
2. 追问皮损类型：粉刺、丘疹、脓疱、结节，是否有瘢痕。
3. 追问诱因：熬夜、压力、饮食、月经周期、护肤和化妆习惯。
4. 红旗：结节囊肿明显、瘢痕加重、心理困扰严重，建议皮肤科就诊。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
