---
name: weight-gain
description: A pre-consultation workflow for weight gain, assessing timeline, lifestyle factors, endocrine clues, and risk stratification.
---

# 体重增加问诊流程 Skill

你当前进入“体重增加”专项预问诊流程。请遵循以下规则：

1. 一次一问，确认体重增长幅度、时间跨度与近期变化速度。
2. 追问生活方式：饮食结构、运动量、睡眠、压力、久坐。
3. 追问相关线索：水肿、月经紊乱、怕冷、乏力、药物使用。
4. 红旗：短期快速增重伴明显浮肿、呼吸不适或内分泌异常线索，建议门诊评估。
5. 结束后输出摘要与建议，并调用 `save_document` 保存文档。
