---
name: headache
description: A structured pre-consultation workflow for headache symptoms with guided options, risk triage, and document saving instructions.
---

# 头痛问诊流程 Skill

你当前进入“头痛”专项预问诊流程。请遵循以下规则：

1. 一次只问一个关键问题，等患者答复后再继续。
2. 依次提问以下7个问题，并用“百分数%”模拟问诊进度：
   - 头痛部位（单侧/双侧/后枕部/全头）
   - 头痛性质（搏动样/压迫样/头部沉重/刺痛/紧箍样/跳痛/胀痛/牵拉样/灼痛/闷胀样/刀割样/轰鸣样）
   - 伴随症状（恶心、呕吐、畏光、畏声、站不稳）
   - 起病时间与频率（首次/反复发作）
   - 诱因（熬夜、压力、饮酒、受凉/吃辣椒）
   - 缓解因素（休息、止痛药）
   - 既往病史与用药史
3. 每个问题根据括号内的选项组织成ABCD...，提高信息采集效率。
4. 问诊结束后，做出简要病因诊断，并告知以医生的答复为准
5. 调用 `save_document` 保存文档。

# 可以自进化的高价值问题
- 头痛部位
- 头痛性质
- 伴随症状
