---
name: back-pain
description: A pre-consultation workflow for back pain with posture, strain, and neurological risk assessment.
---

# 背痛问诊流程 Skill

你当前进入“背痛”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认上背/中背/下背位置与疼痛性质。
2. 追问诱因：久坐姿势不良、运动拉伤、外伤、负重。
3. 追问伴随症状：发热、胸闷、呼吸痛、肢体麻木无力。
4. 红旗：外伤后持续加重、发热伴背痛、神经功能异常，建议及时就医。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
