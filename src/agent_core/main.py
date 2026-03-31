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
from agent_core.skill_router import (
    detect_skill_key,
    get_evolvable_fields,
    get_skill_label,
    load_skill_prompt,
)
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


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        return {}

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {}

    try:
        data = json.loads(text[start:end + 1])
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _find_last_assistant_text(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
    return ""


def detect_headache_option_evolution(
    user_input: str,
    last_assistant_text: str,
    evolvable_fields: list[str],
) -> dict[str, str] | None:
    """
    让模型判断当前用户回答是否应追加为头痛 skill 新选项.
    """
    if not user_input.strip() or not last_assistant_text.strip():
        return None
    if not evolvable_fields:
        return None

    judge_system_prompt = (
        "你是一个问诊技能进化判断器。"
        "请严格输出 JSON 对象，不要输出其他文本。"
    )
    judge_user_prompt = (
        "任务：判断患者回答是否属于“已有字段的新选项”。\n"
        f"可进化字段：{', '.join(evolvable_fields)}\n"
        f"上一轮医生提问：{last_assistant_text}\n"
        f"本轮患者回答：{user_input}\n\n"
        "输出格式：\n"
        "{\n"
        '  "should_append": true/false,\n'
        '  "field_label": "头痛性质 或 头痛部位 或 伴随症状 或 空字符串",\n'
        '  "new_option": "候选词或短语，若不追加则空字符串"\n'
        "}\n\n"
        "规则：\n"
        "1) 仅在患者回答是某个字段的具体表达且不明显属于闲聊时才 should_append=true。\n"
        "2) new_option 必须是简短词组（2-12字），不能包含括号和斜杠。\n"
        "3) 无法确定时返回 should_append=false。"
    )

    try:
        response = httpx.post(
            CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_ID,
                "messages": [
                    {"role": "system", "content": judge_system_prompt},
                    {"role": "user", "content": judge_user_prompt},
                ],
                "max_tokens": 256,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    choice = (data.get("choices") or [{}])[0]
    content = ((choice.get("message") or {}).get("content") or "").strip()
    result = _extract_json_object(content)

    should_append = bool(result.get("should_append"))
    field_label = str(result.get("field_label") or "").strip()
    new_option = str(result.get("new_option") or "").strip()

    if not should_append:
        return None
    if field_label not in evolvable_fields:
        return None
    if len(new_option) < 2 or len(new_option) > 12:
        return None
    if any(ch in new_option for ch in ("\n", "\r", "（", "）", "(", ")", "/")):
        return None

    return {
        "field_label": field_label,
        "new_option": new_option,
    }


def agent_loop() -> None:
    """主 agent 循环 -- 带工具调用的 REPL."""

    messages: list[dict[str, Any]] = []
    openai_tools = _to_openai_tools(TOOLS)
    active_skill_key: str | None = None
    active_skill_prompt = ""

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

        # --- 症状路由: 根据患者描述加载对应 skill ---
        detected_skill = detect_skill_key(user_input)
        if detected_skill and detected_skill != active_skill_key:
            skill_prompt = load_skill_prompt(detected_skill)
            if skill_prompt:
                active_skill_key = detected_skill
                active_skill_prompt = skill_prompt
                print_info(f"[skill_loaded] {get_skill_label(detected_skill)}")

        # --- skills 自进化(最小版): 仅头痛场景追加新选项 ---
        if active_skill_key == "headache":
            evolvable_fields = get_evolvable_fields("headache")
            last_assistant_text = _find_last_assistant_text(messages[:-1])
            evolution = detect_headache_option_evolution(
                user_input=user_input,
                last_assistant_text=last_assistant_text,
                evolvable_fields=evolvable_fields,
            )
            if evolution:
                result = process_tool_call(
                    "append_skill_option",
                    {
                        "skill_key": "headache",
                        "field_label": evolution["field_label"],
                        "new_option": evolution["new_option"],
                    },
                )
                print_info(f"[skill_evolve] {result}")
                if result.startswith("Successfully"):
                    refreshed = load_skill_prompt("headache")
                    if refreshed:
                        active_skill_prompt = refreshed

        while True:
            # --- 调用 LLM ---
            try:
                system_prompt = SYSTEM_PROMPT
                if active_skill_prompt:
                    system_prompt = (
                        f"{SYSTEM_PROMPT.strip()}\n\n"
                        f"## 已激活症状专项 Skill: {get_skill_label(active_skill_key or '')}\n"
                        f"{active_skill_prompt}"
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
