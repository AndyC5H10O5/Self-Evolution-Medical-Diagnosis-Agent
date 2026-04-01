from __future__ import annotations

"""
技能自进化已迁移为工具调用模式。

该模块保留为轻量兼容层，避免旧引用彻底失效。
实际的写入与校验逻辑在 `tools.skill_evolve_tool` 中实现。
"""

from tools.skill_evolve_tool import tool_skill_evolve


def skill_evolve(skill_key: str, field_label: str, new_option: str) -> str:
    """
    兼容入口：直接调用工具侧实现，不触发额外模型请求。
    """
    return tool_skill_evolve(
        skill_key=skill_key,
        field_label=field_label,
        new_option=new_option,
    )
