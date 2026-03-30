from __future__ import annotations

from datetime import datetime
from pathlib import Path

# 项目根目录: .../Consult_Medical_Agent
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SAVE_DIR = PROJECT_ROOT / "documents"


def _safe_path(raw_path: str) -> Path:
    """
    将传入路径约束在项目根目录内, 防止路径穿越.
    """
    target = (PROJECT_ROOT / raw_path).resolve()
    if not str(target).startswith(str(PROJECT_ROOT)):
        raise ValueError(f"Path traversal blocked: {raw_path}")
    return target


def tool_save_document(
    content: str,
    file_path: str | None = None,
    patient_name: str | None = None,
) -> str:
    """
    保存问诊文档到本地.
    - content: 文档正文
    - file_path: 可选, 相对项目根目录路径
    - patient_name: 可选, 用于自动生成文件名
    """
    if not content or not content.strip():
        return "Error: content is empty."

    try:
        if file_path:
            target = _safe_path(file_path)
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = (patient_name or "patient").strip().replace(" ", "_")
            target = DEFAULT_SAVE_DIR / f"{safe_name}_{stamp}.md"

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        rel = target.relative_to(PROJECT_ROOT)
        return f"Successfully saved document to: {rel}"
    except ValueError as exc:
        return f"Error: {exc}"
    except Exception as exc:
        return f"Error: failed to save document: {exc}"


SAVE_DOCUMENT_TOOL = {
    "name": "save_document",
    "description": (
        "Save diagnosis or consultation document to a local file. "
        "Use this after medical pre-consultation is complete."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The document content to save.",
            },
            "file_path": {
                "type": "string",
                "description": (
                    "Optional target file path relative to project root, "
                    "for example: documents/case_001.md"
                ),
            },
            "patient_name": {
                "type": "string",
                "description": (
                    "Optional patient name for auto-generated filename "
                    "when file_path is not provided."
                ),
            },
        },
        "required": ["content"],
    },
}
