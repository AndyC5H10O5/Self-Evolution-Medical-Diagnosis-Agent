import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)

MODEL_ID = os.getenv("MODEL_ID", "deepseek-chat")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
CHAT_COMPLETIONS_URL = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"

SYSTEM_PROMPT = """
## 角色
你是一个医学门诊大夫，需要进行多轮“预问诊”以收集病人的基础信息与病情，并整理成简单诊断书以备使用。
## 任务（CoT）
进行多轮“预问诊”，收集病人信息，一次只问一个关键问题，并适当引导，提供几个可能的选项，确保患者回答。
"""

# ---------------------------------------------------------------------------
# ANSI 颜色
# ---------------------------------------------------------------------------
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"


def colored_prompt() -> str:
    return f"{CYAN}{BOLD}You > {RESET}"


def print_assistant(text: str) -> None:
    print(f"\n{GREEN}{BOLD}Assistant:{RESET} {text}\n")


def print_info(text: str) -> None:
    print(f"{DIM}{text}{RESET}")


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


def agent_loop() -> None:
    """主 agent 循环 -- 对话式 REPL."""

    messages: list[dict[str, str]] = []

    print_info("=" * 60)
    print_info("  claw0  |  Section 01: Agent 循环")
    print_info(f"  Model: {MODEL_ID}")
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
                    "max_tokens": 4096,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            print(f"\n{YELLOW}API Error: {exc}{RESET}\n")
            messages.pop()
            continue

        # --- 解析 DeepSeek 返回 ---
        choice = (data.get("choices") or [{}])[0]
        assistant_text = ((choice.get("message") or {}).get("content") or "").strip()
        finish_reason = choice.get("finish_reason")

        if assistant_text:
            print_assistant(assistant_text)
        else:
            print_info("[warning] 模型返回了空内容.")

        if finish_reason:
            print_info(f"[finish_reason={finish_reason}]")

        messages.append({
            "role": "assistant",
            "content": assistant_text,
        })


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
