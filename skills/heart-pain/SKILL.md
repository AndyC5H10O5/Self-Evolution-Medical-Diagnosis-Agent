---
name: heart-pain
description: A structured pre-consultation workflow for heart-area pain with guided options and cardiovascular risk triage.
---

# 心痛问诊流程 Skill

你当前进入“心痛”专项预问诊流程。请遵循以下规则：

1. 一次只问一个关键问题，等患者答复后再继续。
2. 依次提问以下6个问题，并用“百分数%”模拟问诊进度：
   - 疼痛部位（心前区/胸骨后/左胸偏内侧）
   - 疼痛性质（压迫感/紧缩感/刺痛）
   - 发作时长（数分钟/10分钟以上/反复发作）
   - 伴随症状（心悸/气短/出冷汗）
   - 发作场景（活动后/情绪波动后/夜间静息时）
   - 缓解情况（休息后缓解/服药后缓解/体位变化缓解）
3. 每个问题根据括号内的选项组织成ABCD...，提高信息采集效率。
4. 问诊结束后，做出简要病因诊断，并告知以医生的答复为准
5. 调用 `save_document` 保存文档。

# 可以自进化的高价值问题
- 疼痛性质
- 伴随症状
- 发作场景
