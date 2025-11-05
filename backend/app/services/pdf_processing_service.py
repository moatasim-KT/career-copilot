"""
PDF Processing Service for handling PDF parsing and text extraction.
"""

from typing import Dict, Any, Optional
import PyPDF2

class PDFProcessingService:
    """Service for handling PDF parsing and text extraction."""

    def parse_pdf(self, file_path: str) -> str:
        """Parse a PDF and extract text."""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text

_service = None

def get_pdf_processing_service() -> "PDFProcessingService":
    """Get the PDF processing service."""
    global _service
    if _service is None:
        _service = PDFProcessingService()
    return _service
