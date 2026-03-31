# Consult_Medical_Agent

面向“医疗预问诊”的 Agent 项目，通过 **Skills** 模拟医生的问诊场景。  
当前版本已支持：

- 多轮问诊对话循环（REPL）
- 症状路由加载对应问诊 skill（肚子疼/头痛/恶心）
- **混合检索命中 skills（核心）**：硬编码关键词优先，未命中时走 `skills_meta.yaml` + 模型语义 Top-1 回退
- 保存问诊书
- **skills 自进化（最小版）**：在头痛场景中，将患者新表述自动追加到 `skills/headache/SKILL.md` 的问题选项中

## 功能概览

- **对话引导**：一次一问，收集关键信息
- **症状路由**：根据用户**病症描述**自动加载对应**问诊skill** 提示
- **本地落盘**：问诊结束可调用工具保存“问诊书”到 `documents/`
- **动态进化（核心）**：
  - 当前仅对 `headache` skill 生效
  - 自动识别患者“未覆盖选项”的回答
  - 调用**工具**将新选项追加到已有选项列表

## 核心流程

`src/agent_core/main.py` 的运行链路：

1. 读取用户输入并维护消息历史  
2. 症状路由：先硬编码命中，再元数据语义回退（`skill_router.py`）  
3. 加载命中 skill 的 `SKILL.md` 作为专项提示  
4. 在头痛场景执行最小自进化检测（判断是否出现可追加新选项）  
5. 若模型返回 `tool_calls`，执行本地工具并将结果回传模型  
6. 输出最终问诊回复  


## Skills 混合检索

在 `src/agent_core/skill_router.py` 维护：

- `abdominal_pain`（肚子疼）
- `headache`（头痛）
- `nausea`（恶心）

当前检索策略（Hybrid Retrieval）：

1. **硬编码命中**：每个症状维护5-6个高价值关键词，作为字串尝试匹配用户输入（低延迟）。
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

### 1) 环境准备

- Python 3.10+（建议）
- 安装依赖：

```bash
pip install -r requirements.txt
```

### 2) 配置 `.env`

在项目根目录创建 `.env`：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxx
MODEL_ID=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 3) 启动

PowerShell（推荐）：

```bash
powershell -ExecutionPolicy Bypass -File scripts/run_main.ps1
```

CMD：

```bash
scripts\run_main.bat
```

也可直接运行：

```bash
python src/agent_core/main.py
```

退出命令：`quit` / `exit` / `Ctrl+C`

## 当前边界

- 自进化目前只覆盖 `headache`，尚未扩展到其他 skill
- 仍以文本问诊为主，未引入结构化病历 schema
- 未加入自动测试与 CI 流程

## 改进方向

1. 把 `append_skill_option` 扩展到 `abdominal_pain` 和 `nausea`  
2. 增加“候选池 + 人审确认”再落盘机制（降低误追加风险）  
3. 增加单元测试（工具层、路由层、自进化判定层）  

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
│  ├─ skills_meta.yaml           # skills 元数据（目录）
│  ├─ abdominal-pain/
│  │  └─ SKILL.md
│  ├─ headache/
│  │  └─ SKILL.md                # 头痛问诊流程（支持自进化）
│  └─ nausea/
│     └─ SKILL.md
├─ documents/                    # 问诊结果保存目录
├─ scripts/
│  ├─ run_main.ps1               # 统一启动入口
│  └─ run_main.bat
└─ README.md
```
