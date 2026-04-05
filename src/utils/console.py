from typing import Any

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"


def colored_prompt() -> str:
    return f"{CYAN}{BOLD}You > {RESET}"


def print_assistant(text: str) -> None:
    print(f"\n{GREEN}{BOLD}Assistant:{RESET} {text}\n")


def print_info(text: str) -> None:
    print(f"{DIM}{text}{RESET}")


def print_tool_call(tool_name: str, args: dict[str, Any] | None = None) -> None:
    """
    工具调用日志：skill_evolve 使用高亮，便于终端区分自进化与其它工具。
    """
    if tool_name == "skill_evolve":
        a = args or {}
        sk = str(a.get("skill_key", "") or "").strip()
        fl = str(a.get("field_label", "") or "").strip()
        opt = str(a.get("new_option", "") or "").strip()
        head = f"{MAGENTA}{BOLD}[tool_call] skill_evolve{RESET}"
        if sk or fl or opt:
            detail = (
                f" {DIM}|{RESET} skill_key={CYAN}{sk}{RESET}"
                f" {DIM}|{RESET} field={YELLOW}{fl}{RESET}"
                f" {DIM}|{RESET} new_option={YELLOW}{opt}{RESET}"
            )
            print(head + detail)
        else:
            print(head)
        return
    if tool_name == "submit_evolution_candidate":
        a = args or {}
        sk = str(a.get("skill_key", "") or "").strip()
        fl = str(a.get("field_label", "") or "").strip()
        opt = str(a.get("candidate_option", "") or "").strip()
        head = f"{MAGENTA}{BOLD}[tool_call] submit_evolution_candidate{RESET}"
        detail = (
            f" {DIM}|{RESET} skill_key={CYAN}{sk}{RESET}"
            f" {DIM}|{RESET} field={YELLOW}{fl}{RESET}"
            f" {DIM}|{RESET} candidate={YELLOW}{opt}{RESET}"
        )
        print(head + detail)
        return
    print_info(f"[tool_call] {tool_name}")


def print_skill_evolve_judge(
    skill: str,
    should_append: bool,
    field: str,
    new_option: str,
    reason: str,
) -> None:
    """
    高亮展示自进化判定结果，便于终端快速观察。
    """
    status = "APPEND" if should_append else "SKIP"
    status_color = GREEN if should_append else RED
    field_text = field or "-"
    option_text = new_option or "-"
    reason_text = reason or "-"
    print(
        f"{MAGENTA}{BOLD}[skill_evolve_judge]{RESET} "
        f"skill={CYAN}{skill}{RESET} | "
        f"status={status_color}{BOLD}{status}{RESET} | "
        f"field={YELLOW}{field_text}{RESET} | "
        f"new_option={YELLOW}{option_text}{RESET} | "
        f"reason={DIM}{reason_text}{RESET}"
    )
