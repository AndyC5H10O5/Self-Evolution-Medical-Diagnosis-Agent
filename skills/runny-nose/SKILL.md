---
name: runny-nose
description: A structured pre-consultation workflow for runny nose with guided options and infection/allergy differentiation.
---

# 流鼻涕问诊流程 Skill

你当前进入“流鼻涕”专项预问诊流程。请遵循以下规则：

1. 一次只问一个关键问题，等患者答复后再继续。
2. 依次提问以下6个问题，并用“百分数%”模拟问诊进度：
   - 鼻涕类型（清水样/黏稠白色/黄绿色）
   - 持续时间（当天开始/2-3天/一周以上）
   - 鼻部症状（鼻塞/打喷嚏/鼻痒）
   - 全身症状（发热/咽痛/咳嗽）
   - 触发因素（受凉后/花粉粉尘/晨起明显）
   - 缓解方式（休息后/抗过敏药/感冒药）
3. 每个问题根据括号内的选项组织成ABCD...，提高信息采集效率。
4. 问诊结束后，做出简要病因诊断，并告知以医生的答复为准
5. 调用 `save_document` 保存文档。

# 可以自进化的高价值问题
- 鼻涕类型
- 触发因素
- 全身症状
