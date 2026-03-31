# Consult_Medical_Agent

一个用于学习和实现“医疗预问诊 Agent”的 Python 项目。  
当前主线代码实现了**基础对话循环（无工具调用）**，并在 `模仿/s02_tool_use.py` 中提供了**带工具调用的进阶参考实现**。

## 这个项目在做什么

- 让模型扮演门诊医生，进行多轮预问诊（提问、收集病情信息）。
- 在终端 REPL 中持续对话，维护消息历史。
- 通过 DeepSeek Chat Completions API 获取回复。
- 为后续扩展“工具调用写诊断书/保存本地文件”等能力打基础。

## 当前代码状态（重点）

- **主入口**：`src/agent_core/main.py`
  - 已实现用户输入 -> 调用模型 -> 输出回复的循环。
  - 当前只处理常规文本回复（`finish_reason` 打印出来用于观察状态）。
  - 尚未在主线接入工具调用（tool use）。
- **配置模块**：`src/config/settings.py`
  - 从 `.env` 读取 `DEEPSEEK_API_KEY`、`MODEL_ID`、`DEEPSEEK_BASE_URL`。
  - 组装 `CHAT_COMPLETIONS_URL`。
- **系统提示词**：`src/config/sys_prompts.py`
  - 定义医疗预问诊角色和任务目标（逐步提问、结束后生成诊断书等）。
- **终端输出样式**：`src/utils/console.py`
  - 封装彩色 prompt、助手输出、信息输出。
- **进阶参考（非主线）**：`模仿/s02_tool_use.py`
  - 展示如何在 Agent 循环中处理 `tool_use`/`tool_result`。
  - 内置 `bash/read_file/write_file/edit_file` 工具与分发表，包含基础安全校验。

## 目录速览

```text
Consult_Medical_Agent/
├─ src/
│  ├─ agent_core/
│  │  └─ main.py              # 主线：基础 agent 循环
│  ├─ config/
│  │  ├─ settings.py          # 环境变量与 API 地址配置
│  │  └─ sys_prompts.py       # 医疗预问诊系统提示词
│  └─ utils/
│     └─ console.py           # 终端彩色输出工具
├─ 模仿/
│  └─ s02_tool_use.py         # 参考：带工具调用的 agent 版本
└─ README.md
```

## 主流程（`src/agent_core/main.py`）

1. 启动时检查 `DEEPSEEK_API_KEY` 是否存在。  
2. 进入 REPL 循环读取用户输入。  
3. 将用户消息追加到 `messages`。  
4. 发送请求到 `CHAT_COMPLETIONS_URL`（`httpx.post`）。  
5. 解析 `choices[0].message.content` 并输出。  
6. 将 assistant 回复追加回历史，进入下一轮。  

说明：主线版本保留了 Agent 循环骨架，适合作为后续接入工具调用的最小实现。

## 快速运行

## 1) 环境准备

- Python 3.10+（建议）
- 安装依赖（按代码推断最少）：

```bash
pip install httpx python-dotenv
```

如果你要运行 `模仿/s02_tool_use.py`，还需要该脚本依赖的兼容 SDK（例如其中导入的 `deepseek_compat` 相关包）。

## 2) 配置 `.env`

在项目根目录创建 `.env`：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxx
MODEL_ID=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

## 3) 启动主线 Agent（推荐统一缓存目录）

```bash
powershell -ExecutionPolicy Bypass -File scripts/run_main.ps1
```

输入 `quit` 或 `exit` 或 `ctrl+C`退出。

如需在 CMD 中启动，可使用：

```bash
scripts\run_main.bat
```

若你仍想手动执行 Python 命令，请先设置：

```bash
set PYTHONPYCACHEPREFIX=.cache\pycache
python src/agent_core/main.py
```

## 已知限制

- 主线尚未实现工具调用闭环（例如自动保存诊断书到本地）。
- 暂无结构化病历/诊断书的数据模型（目前是纯文本对话）。
- 暂无测试、依赖清单文件（如 `requirements.txt`/`pyproject.toml`）。

## 后续建议（按优先级）

1. 设计“诊断书”结构化格式（JSON/Markdown 模板）并新增保存工具。  
2. 增加最小依赖文件（`requirements.txt`）和启动说明脚本。  
3. 为关键流程补充基础测试（配置加载、API 响应解析、工具分发）。  