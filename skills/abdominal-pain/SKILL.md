---
name: abdominal-pain
description: A structured pre-consultation workflow for abdominal pain symptoms with guided options and risk triage.
---

# 肚子痛问诊流程 Skill

你当前进入“肚子痛（腹痛）”专项预问诊流程。请遵循以下规则：

1. 一次只问一个关键问题，等患者答复后再继续。
2. 依次提问以下6个问题，并用“百分数%”模拟问诊进度：
   - 疼痛部位（上腹/下腹/左下腹）
   - 疼痛性质（绞痛/钝痛/刺痛）
   - 持续时间（突发/逐渐/间歇）
   - 伴随症状（发热/呕吐/腹泻）
   - 诱因（进食后/空腹时/受凉后）
   - 缓解因素（休息后缓解/排便后缓解/热敷后缓解）
3. 每个问题根据括号内的选项组织成ABCD...，提高信息采集效率。
4. 问诊结束后，做出简要病因诊断，并告知以医生的答复为准
5. 调用 `save_document` 保存文档。

# 可以自进化的高价值问题
- 疼痛部位
- 疼痛性质
- 伴随症状
