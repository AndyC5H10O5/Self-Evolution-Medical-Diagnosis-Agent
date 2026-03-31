# Self-Evolution: Medical Diagnosis Agent


面向“医疗预问诊”的 Agent 项目。  
项目核心能力是 **Skills 混合检索** 和 **Skills 自进化**。

## 当前已实现

- 多轮对话问诊（REPL）
- 工具调用闭环（`tool_calls` -> 本地执行 -> `tool` 回传）
- 本地文档保存（`save_document`）
- Skills 混合检索：
  - **关键词匹配**：**高价值关键词**通过硬编码快速命中（低延迟）
  - **语义检索**：硬编码未命中时，读取 `skills/skills_meta.yaml`，即模型通过自然语言处理查看 **Skills目录**
- Skills 自进化：
  - 支持所有症状 skill 的问诊流程**动态升级**（按各自 `evolvable_fields` 生效）
  - 未覆盖回答可自动追加到对应 `skills/<skill-name>/SKILL.md` 选项中（由 `agent_core/skill_evolve.py` 执行）



## Skills 混合检索

当前检索策略（Hybrid Retrieval）：

1. **硬编码命中**：每个症状维护5个高价值关键词，作为字串尝试匹配用户输入（低延迟）。
2. **语义检索**：硬编码未命中时，读取 `skills/skills_meta.yaml`，即模型按 自然语言查看 **Skills目录**



每个症状在 `skills/skills_meta.yaml` 中均维护 `evolvable_fields`，用于限定该症状可进化的高价值问题集合。

## Skills 自进化（全症状可用）

目标：提升问诊选项覆盖率。  
机制：检测 -> 判断 -> 追加 -> 立即生效。

示例（`skills/headache/SKILL.md`）：

- 原始：`头痛性质（搏动样/压迫样/刺痛）`
- 患者回答：`头部沉重`
- **进化后**：`头痛性质（搏动样/压迫样/刺痛/头部沉重）`

说明：

- 直接改写当前激活症状对应的 `skills/<skill-name>/SKILL.md`
- 暂未实现版本控制与人工审核（MVP 约束）
- 重复词条不会重复追加
- 每次追加前会在终端显示输出 `skill_evolve_judge` 判定结果（是否追加、字段、候选项、原因）

## Skills 覆盖范围

当前共维护 21 个症状 skill：

- `headache`（头痛）
- `insomnia`（失眠）
- `tinnitus`（耳鸣）
- `eye_pain`（眼痛）
- `runny_nose`（流鼻涕）
- `chest_pain`（胸痛）
- `heart_pain`（心痛）
- `sore_throat`（喉咙痛）
- `cough`（咳嗽）
- `abdominal_pain`（肚子痛）
- `diarrhea`（腹泻）
- `vomiting`（呕吐）
- `joint_pain`（关节痛）
- `waist_pain`（腰痛）
- `back_pain`（背痛）
- `leg_pain`（腿痛）
- `fever`（发烧）
- `fatigue`（疲劳）
- `acne`（痤疮）
- `weight_gain`（体重增加）
- `nausea`（恶心）

每个症状在硬编码路由中维护 5 个高价值关键词。


## 已接入工具

在 `src/tools/__init__.py` 注册：

- `save_document`
  - 保存诊断/问诊文档到本地
  - 支持自动文件名或指定 `file_path`

自进化相关能力由 `src/agent_core/skill_evolve.py` 内部实现（识别新选项 + 追加写回），不再通过独立工具注册暴露。

## 快速开始

### 1) 安装依赖

```bash
pip install -r requirements.txt
```

### 2) 配置 `.env`

```env
DEEPSEEK_API_KEY=sk-xxxxxxxx
MODEL_ID=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 3) 启动

PowerShell：

```bash
powershell -ExecutionPolicy Bypass -File scripts/run_main.ps1
```

CMD：

```bash
scripts\run_main.bat
```

或直接：

```bash
python src/agent_core/main.py
```

退出：`quit` / `exit` / `Ctrl+C`

## 项目结构

```text
Consult_Medical_Agent/
├─ src/
│  ├─ agent_core/
│  │  ├─ main.py                 # 主循环：Agent loop、tool call、自进化
│  │  ├─ skill_router.py         # 症状识别与 skills 路由
│  │  ├─ skill_router_NLP.py     # 元数据语义回退路由
│  │  └─ skill_evolve.py         # 全症状自进化模块（识别+追加）
│  ├─ tools/
│  │  ├─ __init__.py             # 工具注册表
│  │  └─ save_document.py        # 保存问诊文档
│  ├─ config/
│  │  ├─ settings.py             # .env 配置加载
│  │  └─ sys_prompts.py          # 系统提示词
│  └─ utils/
│     └─ console.py              # 终端输出样式
├─ skills/
│  ├─ skills_meta.yaml           # 问诊结果保存目录
│  └─ <skill-name>/SKILL.md      # 问诊流程（支持自进化）
├─ documents/                    # 问诊结果保存目录
├─ scripts/
│  ├─ run_main.ps1               # 统一启动入口
│  └─ run_main.bat
└─ README.md
```
