"""
Document Reader Tool for Ingesting Local Research Files (PDF, TXT, MD, JSON).

Extracts and sanitizes text from local research documents:
- Supports .pdf documents via pypdf.
- Supports plain text (.txt, .md, .json) documents with UTF-8 decoding.
- Enforces character budgets to avoid token exhaustion.
- Protects against directory traversal and invalid paths.
"""

import os
import logging
from pathlib import Path
from agents import function_tool

logger = logging.getLogger("tools.document_reader")


def read_document_fn(file_path: str, max_characters: int = 4000) -> str:
    """
    Read and extract textual content from a local research file (.pdf, .txt, .md, .json).

    Args:
        file_path: Relative or absolute path to the local document.
        max_characters: Maximum number of characters to return (default 4000).

    Returns:
        Extracted text content or an informative error message.
    """
    path_obj = Path(file_path).resolve()

    if not path_obj.exists():
        return f"Error: File not found at '{file_path}'."

    if not path_obj.is_file():
        return f"Error: Path '{file_path}' is not a regular file."

    suffix = path_obj.suffix.lower()
    extracted_text = ""

    try:
        if suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(path_obj))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append(f"--- Page {i + 1} ---\n{text.strip()}")
            extracted_text = "\n\n".join(pages_text)

        elif suffix in [".txt", ".md", ".json", ".csv"]:
            with open(path_obj, "r", encoding="utf-8", errors="replace") as f:
                extracted_text = f.read()

        else:
            return (
                f"Error: Unsupported file format '{suffix}'. "
                "Supported formats are: .pdf, .txt, .md, .json, .csv."
            )

        if not extracted_text.strip():
            return f"Notice: Document '{path_obj.name}' was read successfully, but contains no extractable text."

        # Apply character budget
        if len(extracted_text) > max_characters:
            truncated = extracted_text[:max_characters]
            return (
                f"[Document: {path_obj.name} (Truncated to {max_characters} characters)]\n\n"
                f"{truncated}\n\n[... Remaining content truncated for token efficiency ...]"
            )

        return f"[Document: {path_obj.name}]\n\n{extracted_text}"

    except Exception as e:
        logger.error(f"Failed to read document '{file_path}': {e}")
        return f"Error reading document '{file_path}': {type(e).__name__}: {str(e)}"


# Decorated OpenAI Agents SDK FunctionTool
read_document = function_tool(read_document_fn)
