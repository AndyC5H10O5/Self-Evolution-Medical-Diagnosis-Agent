import sys
from pathlib import Path
import httpx
import json
from typing import Any

# 允许直接运行 `python src/agent_core/main.py` 时解析 `src` 下的绝对导入
SRC_ROOT = Path(__file__).resolve().parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config.settings import CHAT_COMPLETIONS_URL, DEEPSEEK_API_KEY, MODEL_ID
from config.sys_prompts import SYSTEM_PROMPT
from tools import TOOL_HANDLERS, TOOLS
from utils.console import DIM, RESET, YELLOW, colored_prompt, print_assistant, print_info

# ---------------------------------------------------------------------------
# 核心: Agent 循环
# ---------------------------------------------------------------------------
#   1. 收集用户输入, 追加到 messages
#   2. 调用 API
#   3. 检查 stop_reason 决定下一步
#
#   本节 stop_reason 永远是 "end_turn" (没有工具).
#   下一节加入 "tool_use" -- 循环结构保持不变.
# ---------------------------------------------------------------------------


def _to_openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    将参考实现里的工具 schema 转成 chat/completions 的 tools 格式.
    """
    converted: list[dict[str, Any]] = []
    for tool in tools:
        converted.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
            },
        })
    return converted


def process_tool_call(tool_name: str, tool_input: dict[str, Any]) -> str:
    """
    根据工具名分发到对应处理函数.
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return f"Error: Unknown tool '{tool_name}'"

    try:
        return handler(**tool_input)
    except TypeError as exc:
        return f"Error: Invalid arguments for {tool_name}: {exc}"
    except Exception as exc:
        return f"Error: {tool_name} failed: {exc}"


def agent_loop() -> None:
    """主 agent 循环 -- 带工具调用的 REPL."""

    messages: list[dict[str, Any]] = []
    openai_tools = _to_openai_tools(TOOLS)

    print_info("=" * 60)
    print_info("  claw0  |  Agent 循环 + Tool Use")
    print_info(f"  Model: {MODEL_ID}")
    print_info(f"  Tools: {', '.join(TOOL_HANDLERS.keys())}")
    print_info("  输入 'quit' 或 'exit' 退出. Ctrl+C 同样有效.")
    print_info("=" * 60)
    print()

    while True:
        # --- 获取用户输入 ---
        try:
            user_input = input(colored_prompt()).strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}再见.{RESET}")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print(f"{DIM}再见.{RESET}")
            break

        # --- 追加到历史 ---
        messages.append({
            "role": "user",
            "content": user_input,
        })

        while True:
            # --- 调用 LLM ---
            try:
                payload_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
                response = httpx.post(
                    CHAT_COMPLETIONS_URL,
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": MODEL_ID,
                        "messages": payload_messages,
                        "tools": openai_tools,
                        "tool_choice": "auto",
                        "max_tokens": 4096,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                print(f"\n{YELLOW}API Error: {exc}{RESET}\n")
                messages.pop()
                break

            # --- 解析返回 ---
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            finish_reason = choice.get("finish_reason")
            assistant_text = (message.get("content") or "").strip()
            tool_calls = message.get("tool_calls") or []

            # 先把 assistant 消息放入历史(包含 tool_calls)
            assistant_record: dict[str, Any] = {"role": "assistant", "content": message.get("content")}
            if tool_calls:
                assistant_record["tool_calls"] = tool_calls
            messages.append(assistant_record)

            if finish_reason == "tool_calls" and tool_calls:
                for tool_call in tool_calls:
                    func = tool_call.get("function") or {}
                    tool_name = func.get("name", "")
                    raw_args = func.get("arguments") or "{}"

                    try:
                        args = json.loads(raw_args)
                        if not isinstance(args, dict):
                            args = {}
                    except Exception:
                        args = {}

                    print_info(f"[tool_call] {tool_name}")
                    result = process_tool_call(tool_name, args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", ""),
                        "name": tool_name,
                        "content": result,
                    })
                # 继续内循环, 把工具结果交回模型
                continue

            if assistant_text:
                print_assistant(assistant_text)
            else:
                print_info("[warning] 模型返回了空内容.")

            if finish_reason:
                print_info(f"[finish_reason={finish_reason}]")

            break


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main() -> None:
    if not DEEPSEEK_API_KEY:
        print(f"{YELLOW}Error: DEEPSEEK_API_KEY 未设置.{RESET}")
        print(f"{DIM}将 .env.example 复制为 .env 并填入你的 key.{RESET}")
        sys.exit(1)

    agent_loop()


if __name__ == "__main__":
    main()
