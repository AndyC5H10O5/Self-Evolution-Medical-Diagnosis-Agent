---
name: fever
description: A pre-consultation workflow for fever to assess duration, associated symptoms, exposure history, and danger signs.
---

# 发烧问诊流程 Skill

你当前进入“发烧”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认体温范围、起病时间、是否反复发热。
2. 追问伴随症状：咳嗽、咽痛、腹泻、尿频尿痛、皮疹、头痛。
3. 追问暴露史：近期感染接触、旅行、基础病、免疫抑制状态。
4. 红旗：高热持续不退、意识改变、呼吸困难、惊厥，建议急诊。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
