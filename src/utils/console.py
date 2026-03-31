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
