from tools.save_document import SAVE_DOCUMENT_TOOL, tool_save_document

TOOLS = [SAVE_DOCUMENT_TOOL]

TOOL_HANDLERS = {
    "save_document": tool_save_document,
}
