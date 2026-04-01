from tools.save_document import SAVE_DOCUMENT_TOOL, tool_save_document
from tools.skill_evolve_tool import SKILL_EVOLVE_TOOL, tool_skill_evolve

TOOLS = [SAVE_DOCUMENT_TOOL, SKILL_EVOLVE_TOOL]

TOOL_HANDLERS = {
    "save_document": tool_save_document,
    "skill_evolve": tool_skill_evolve,
}
