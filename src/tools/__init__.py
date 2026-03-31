from tools.save_document import SAVE_DOCUMENT_TOOL, tool_save_document
from tools.append_skill_option import APPEND_SKILL_OPTION_TOOL, tool_append_skill_option

TOOLS = [SAVE_DOCUMENT_TOOL, APPEND_SKILL_OPTION_TOOL]

TOOL_HANDLERS = {
    "save_document": tool_save_document,
    "append_skill_option": tool_append_skill_option,
}
