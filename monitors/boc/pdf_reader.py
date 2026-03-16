"""PDF download and content extraction module."""

import logging
import os
import tempfile
from typing import Optional

import requests

import config

log = logging.getLogger("monitor")


class PDFReader:
    """PDF file processor."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
        })

    def download_pdf(self, url: str) -> Optional[str]:
        """Download PDF file to temp directory.

        Returns temp file path, or None on failure.
        """
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()

            fd, temp_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)

            with open(temp_path, 'wb') as f:
                f.write(response.content)

            return temp_path
        except requests.RequestException as e:
            log.error(f"Failed to download PDF: {url}, error: {e}")
            return None
        except IOError as e:
            log.error(f"Failed to save PDF: {e}")
            return None

    def extract_text(self, pdf_path: str) -> str:
        """Extract PDF text content.

        Uses pdfplumber first, then PyMuPDF as fallback.
        """
        if not pdf_path or not os.path.exists(pdf_path):
            return ""

        text = ""

        try:
            text = self._extract_with_pdfplumber(pdf_path)
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            log.error(f"pdfplumber extraction failed: {e}")

        try:
            import fitz
            text = self._extract_with_fitz(pdf_path)
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            log.error(f"PyMuPDF extraction failed: {e}")

        return text

    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber."""
        import pdfplumber

        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return '\n\n'.join(text_parts)

    def _extract_with_fitz(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF."""
        import fitz

        text_parts = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_parts.append(page.get_text())
        doc.close()

        return '\n\n'.join(text_parts)

    def cleanup(self, pdf_path: str):
        """Clean up temp PDF file."""
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError:
                pass

    def download_and_extract(self, url: str) -> str:
        """Download PDF and extract content (combined method)."""
        pdf_path = self.download_pdf(url)
        if not pdf_path:
            return ""

        try:
            text = self.extract_text(pdf_path)
            return text
        finally:
            self.cleanup(pdf_path)