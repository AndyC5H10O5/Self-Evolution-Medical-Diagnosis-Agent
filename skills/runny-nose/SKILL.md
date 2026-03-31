---
name: runny-nose
description: A pre-consultation workflow for runny nose focused on infectious versus allergic patterns and respiratory risk signs.
---

# 流鼻涕问诊流程 Skill

你当前进入“流鼻涕”专项预问诊流程。请遵循以下规则：

1. 一次只问一个关键问题，确认清水样或脓性鼻涕、持续时长与频次。
2. 追问伴随症状：打喷嚏、鼻塞、咽痛、发热、咳嗽、眼痒。
3. 识别倾向：感冒感染、过敏性鼻炎、鼻窦炎线索。
4. 红旗：高热持续、面部明显疼痛、呼吸困难，建议及时线下就医。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
