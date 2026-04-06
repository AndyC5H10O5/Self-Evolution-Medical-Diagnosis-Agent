---
name: waist-pain
description: A structured pre-consultation workflow for waist pain with guided options and neurological red-flag screening.
---

# 腰痛问诊流程 Skill

你当前进入“腰痛”专项预问诊流程。请遵循以下规则：

1. 一次只问一个关键问题，等患者答复后再继续。
2. 依次提问以下6个问题，并用“百分数%”模拟问诊进度：
   - 疼痛位置（腰中部/左侧腰/右侧腰）
   - 疼痛性质（酸痛/刺痛/胀痛）
   - 病程（突发/逐渐/反复发作）
   - 放射与神经症状（臀部放射/腿麻/腿无力）
   - 诱发因素（久坐/搬重物/扭伤）
   - 缓解情况（休息后/热敷后/止痛药后）
3. 每个问题根据括号内的选项组织成ABCD...，提高信息采集效率。
4. 问诊结束后，做出简要病因诊断，并告知以医生的答复为准
5. 调用 `save_document` 保存文档。

# 可以自进化的高价值问题
- 疼痛性质
- 放射与神经症状
- 诱发因素
