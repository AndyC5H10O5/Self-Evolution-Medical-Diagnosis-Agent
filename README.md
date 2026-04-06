# Self-Evolution: Medical Diagnosis Agent

面向“医疗预问诊”的 Agent 项目。  
项目核心能力是 **Skills 混合检索**、**双 Agent 协作**，以及 **Skills 自进化**（由独立进化器异步落盘）。

## 当前已实现

- 多轮对话问诊（REPL）
- 工具调用闭环（`tool_calls` -> 本地执行 -> `tool` 回传）
- 本地文档保存（`save_document`）
- Skills 混合检索
- **问诊器 + 进化器 双 Agent 协作**（见下文）
- Skills 自进化：
  - 支持各症状 skill 的问诊流程**动态升级**（按各自 `evolvable_fields` 生效）
  - 候选项经进化器判别后，通过 `tools/skill_evolve_tool.py` 追加到 `skills/<skill-name>/SKILL.md`

## 问诊器与进化器（双 Agent）



| 角色 | 入口 | 职责 |
|------|------|------|
| **问诊器** | `src/agent_core/main.py` | 多轮预问诊、加载 skill、调用 `save_document`；发现疑似新选项时仅调用 `submit_evolution_candidate` **上报候选**，不直接改 skill 文件。 |
| **进化器** | `src/evolve_core/main.py` | **异步**读取候选队列，调用模型判别是否进化；若通过则调用现有 `tool_skill_evolve` **写回**对应 `SKILL.md`。 |

协作流程简述：

1. 问诊器在对话中认为患者回答可能是新选项时，调用工具 `submit_evolution_candidate`，将 `skill_key`、`field_label`、`user_turn`、`candidate_option` 等写入队列文件 `runtime/evolution/candidates.jsonl`。
2. 进化器进程持续消费该队列（按行增量、状态记在 `runtime/evolution/consumer_state.json`），结合 **当前 skill 全文** 做判别，再决定是否执行 `skill_evolve`。
3. 问诊与进化 **解耦、无锁**；重复词条由写盘逻辑兜底（已存在则不重复追加）。

本地开发时请 **同时运行两个入口**（例如两个终端），否则候选只会入队、不会被消费。

## Skills 混合检索

当前检索策略（Hybrid Retrieval）：

1. **硬编码命中**：各症状在 `src/config/skill_routes.py` 中维护高价值关键词，对用户输入做子串匹配（低延迟）。
2. **语义检索**：硬编码未命中时，读取 `skills/skills_meta.yaml`，由模型在自然语言层面从 **Skills 目录元数据** 中选择更匹配的 skill。

每个症状在 `skills/skills_meta.yaml` 中可维护 `evolvable_fields`，用于限定该症状允许进化的字段集合。

## Skills 自进化（全症状可用）

目标：在长周期运行后提升问诊 **选项覆盖率**。  
机制：**上报候选** → **进化器异步判别** → **追加写回** → 下次加载 skill 即生效。

示例（`skills/headache/SKILL.md`）：

- 原始：`头痛性质（搏动样/压迫样/刺痛）`
- 患者回答：`头部沉重`
- **进化后**（经进化器确认）：`头痛性质（搏动样/压迫样/刺痛/头部沉重）`

说明：

- 写盘仅通过 `tools/skill_evolve_tool.py`（由进化器调用）
- 暂未实现版本控制与人工审核（MVP 约束）
- 重复词条不会重复追加

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

关键词路由表见 `src/config/skill_routes.py`。

## 已接入工具

在 `src/tools/__init__.py` 中分为两套（问诊器可见 / 进化器内部使用）：

**问诊器可用：**

- `save_document`：保存诊断/问诊文档到本地（支持自动文件名或指定 `file_path`）
- `submit_evolution_candidate`：上报进化候选，**仅入队**，不写 skill

**进化器内部使用（不暴露给问诊器）：**

- `skill_evolve`：追加选项到当前症状 skill 文件（实现于 `tools/skill_evolve_tool.py`）

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

### 3) 启动（两个进程）



**终端 A — 问诊器：**

```bash
python src/agent_core/main.py
```

**终端 B — 进化器：**

```bash
python src/evolve_core/main.py
```

也可使用 VS Code / Cursor 的 **运行和调试**：`.vscode/launch.json` 中已提供「问诊器 agent_core」「进化器 evolve_core」配置。

退出：`quit` / `exit` / `Ctrl+C`

### 4) 评测脚本（暂不可用）

Benchmark 相关脚本位于 `scripts/benchmark/`，用法见 `scripts/benchmark/README.md`。

## 项目结构

```text
Consult_Medical_Agent/
├─ src/
│  ├─ agent_core/
│  │  ├─ main.py                 # 问诊器：Agent loop、工具调用
│  │  ├─ skill_router.py         # 症状识别与 skills 路由（逻辑）
│  │  └─ skill_router_NLP.py     # 元数据语义回退路由
│  ├─ evolve_core/
│  │  ├─ main.py                 # 进化器：消费队列、模型判别、调用 skill_evolve 写盘
│  │  ├─ worker.py               # 候选队列（jsonl + 消费游标）
│  │  └─ schemas.py              # 候选/判别数据结构
│  ├─ tools/
│  │  ├─ __init__.py             # 问诊 / 进化 工具注册表
│  │  ├─ save_document.py
│  │  ├─ evolution_submit_tool.py
│  │  └─ skill_evolve_tool.py    # skill 选项追加（由进化器调用）
│  ├─ config/
│  │  ├─ settings.py             # .env 配置加载
│  │  ├─ sys_prompts.py          # 问诊器 / 进化器 系统提示词
│  │  └─ skill_routes.py         # 症状关键词路由表
│  └─ utils/
│     └─ console.py              # 终端输出样式
├─ skills/
│  ├─ skills_meta.yaml           # skills 元数据目录
│  └─ <skill-name>/SKILL.md      # 问诊流程（可被进化器更新）
├─ runtime/
│  └─ evolution/                 # 进化候选队列（运行期生成）
├─ documents/                    # 问诊结果保存目录
├─ scripts/
│  └─ benchmark/                 # 离线评测脚本
└─ README.md
```
