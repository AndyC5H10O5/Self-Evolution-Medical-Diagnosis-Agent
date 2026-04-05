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
from config.sys_prompts import CONSULT_EVOLUTION_HANDOFF_POLICY_TEMPLATE, SYSTEM_PROMPT
from agent_core.skill_router import (
    detect_skill_key,
    get_evolvable_fields,
    get_skill_label,
    load_skill_prompt,
)
from agent_core.skill_router_NLP import detect_skill_key_by_metadata
from tools import CONSULT_TOOL_HANDLERS, CONSULT_TOOLS
from utils.console import (
    DIM,
    RESET,
    YELLOW,
    colored_prompt,
    print_assistant,
    print_info,
    print_tool_call,
)


def _to_openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    工具 schema 转成 chat/completions 的 tools 格式.
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
    handler = CONSULT_TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return f"Error: Unknown tool '{tool_name}'"

    try:
        return handler(**tool_input)
    except TypeError as exc:
        return f"Error: Invalid arguments for {tool_name}: {exc}"
    except Exception as exc:
        return f"Error: {tool_name} failed: {exc}"


# ---------------------------------------------------------------------------
# 核心: Agent 循环
# ---------------------------------------------------------------------------
#   1. 收集用户输入, 追加到 messages
#   2. 调用 API
#   3. 检查 stop_reason 决定下一步
# ---------------------------------------------------------------------------


def agent_loop() -> None:
    """主 agent 循环 -- 带工具调用的 REPL."""

    messages: list[dict[str, Any]] = []
    openai_tools = _to_openai_tools(CONSULT_TOOLS)
    active_skill_key: str | None = None
    active_skill_prompt = ""

    print_info("=" * 60)
    print_info(f"  Model: {MODEL_ID}")
    print_info(f"  Tools: {', '.join(CONSULT_TOOL_HANDLERS.keys())}")
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

        # --- 症状路由: 根据患者描述加载对应 skill ---
        detected_skill = detect_skill_key(user_input)
        if not detected_skill:
            detected_skill = detect_skill_key_by_metadata(user_input)
            if detected_skill:
                print_info(f"[skill_meta: NLP_hit] {detected_skill}")
        if detected_skill and detected_skill != active_skill_key:
            skill_prompt = load_skill_prompt(detected_skill)
            if skill_prompt:
                active_skill_key = detected_skill
                active_skill_prompt = skill_prompt
                print_info(f"[skill_loaded] {get_skill_label(detected_skill)}.md")

        while True:
            # --- 调用 LLM ---
            try:
                system_prompt = SYSTEM_PROMPT
                if active_skill_prompt:
                    evolvable_fields = get_evolvable_fields(active_skill_key or "")
                    fields_text = ", ".join(evolvable_fields) if evolvable_fields else "（无）"
                    evolution_policy = CONSULT_EVOLUTION_HANDOFF_POLICY_TEMPLATE.format(
                        skill_key=active_skill_key or "",
                        evolvable_fields=fields_text,
                    )
                    system_prompt = (
                        f"{SYSTEM_PROMPT.strip()}\n\n"
                        f"## 已激活症状专项 Skill: {get_skill_label(active_skill_key or '')}\n"
                        f"{active_skill_prompt}\n\n"
                        f"{evolution_policy.strip()}"
                    )

                payload_messages = [{"role": "system", "content": system_prompt}] + messages
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

                    print_tool_call(tool_name, args)
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
