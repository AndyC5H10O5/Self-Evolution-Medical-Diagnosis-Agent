# Consult_Medical_Agent

面向“医疗预问诊”的终端 Agent 项目，基于 DeepSeek Chat Completions API。  
项目核心能力是 **Skills 混合检索**：先走硬编码关键词路由，未命中再走元数据语义检索（Top-1）。

## 当前已实现

- 多轮对话问诊（REPL）
- 工具调用闭环（`tool_calls` -> 本地执行 -> `tool` 回传）
- 本地文档保存（`save_document`）
- Skills 混合检索：
  - 硬编码关键词快速命中（低延迟）
  - `skills/skills_meta.yaml` + `use_when` 语义回退命中
- Skills 自进化（最小版）：
  - 当前仅 `headache` 支持
  - 未覆盖回答可追加到 `skills/headache/SKILL.md` 选项中（`append_skill_option`）

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

## Skills 混合检索

在 `src/agent_core/skill_router.py` 维护：

- `abdominal_pain`（肚子疼）
- `headache`（头痛）
- `nausea`（恶心）

当前检索策略（Hybrid Retrieval）：

1. **硬编码命中**：每个症状维护5个高价值关键词，作为字串尝试匹配用户输入（低延迟）。
2. **语义检索**：硬编码未命中时，读取 `skills/skills_meta.yaml`，即模型按 自然语言查看 **Skills目录**



其中 `headache` 增加了 `evolvable_fields`：

- `头痛部位`
- `头痛性质`
- `伴随症状`

## Skills 自进化（最小可实现）

目标：提升问诊选项覆盖率。  
机制：检测 -> 判断 -> 追加 -> 立即生效。

示例（`skills/headache/SKILL.md`）：

- 原始：`头痛性质（搏动样/压迫样/刺痛）`
- 患者回答：`头部沉重`
- **进化后**：`头痛性质（搏动样/压迫样/刺痛/头部沉重）`

说明：

- 直接改写 `skills/headache/SKILL.md`
- 暂未实现版本控制与人工审核（MVP 约束）
- 重复词条不会重复追加


## 已接入工具

在 `src/tools/__init__.py` 注册：

- `save_document`
  - 保存诊断/问诊文档到本地
  - 支持自动文件名或指定 `file_path`
- `append_skill_option`（核心）
  - 将新选项追加进 skill 的目标字段
  - 当前仅支持 `skill_key=headache`
  - 内置输入校验与去重检测

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
│  │  └─ skill_router.py         # 症状识别与 skills 路由
│  ├─ tools/
│  │  ├─ __init__.py             # 工具注册表
│  │  ├─ save_document.py        # 保存问诊文档
│  │  └─ append_skill_option.py  # 追加 skill 选项（最小版）
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
