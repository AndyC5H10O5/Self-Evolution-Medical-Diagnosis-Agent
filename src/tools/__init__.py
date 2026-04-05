from tools.save_document import SAVE_DOCUMENT_TOOL, tool_save_document
from tools.evolution_submit_tool import (
    SUBMIT_EVOLUTION_CANDIDATE_TOOL,
    tool_submit_evolution_candidate,
)
from tools.skill_evolve_tool import SKILL_EVOLVE_TOOL, tool_skill_evolve

CONSULT_TOOLS = [SAVE_DOCUMENT_TOOL, SUBMIT_EVOLUTION_CANDIDATE_TOOL]
CONSULT_TOOL_HANDLERS = {
    "save_document": tool_save_document,
    "submit_evolution_candidate": tool_submit_evolution_candidate,
}

EVOLVE_TOOLS = [SKILL_EVOLVE_TOOL]
EVOLVE_TOOL_HANDLERS = {
    "skill_evolve": tool_skill_evolve,
}

# 兼容历史导入：默认暴露问诊器工具集
TOOLS = CONSULT_TOOLS
TOOL_HANDLERS = CONSULT_TOOL_HANDLERS
