"""
Tools package providing specialized integrations for multi-agent capabilities:
- search_web: DuckDuckGo live web research
- read_document: PDF, Markdown, and text document extractor
- execute_python_analysis: Sandboxed analytical Python code runner
"""

from .web_search import search_web, search_web_fn
from .document_reader import read_document, read_document_fn
from .python_tool import execute_python_analysis, execute_python_analysis_fn

__all__ = [
    "search_web",
    "search_web_fn",
    "read_document",
    "read_document_fn",
    "execute_python_analysis",
    "execute_python_analysis_fn",
]

from src.tools.pdf_exporter import generate_pdf_report
