"""PDF下载和内容提取模块"""

import logging
import os
import tempfile
from typing import Optional

import requests

import config

log = logging.getLogger("boc_monitor")


class PDFReader:
    """PDF文件处理"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
        })

    def download_pdf(self, url: str) -> Optional[str]:
        """下载PDF文件到临时目录

        返回临时文件路径，失败返回None
        """
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()

            # 创建临时文件
            fd, temp_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)

            with open(temp_path, 'wb') as f:
                f.write(response.content)

            return temp_path
        except requests.RequestException as e:
            log.error(f"下载PDF失败: {url}, 错误: {e}")
            return None
        except IOError as e:
            log.error(f"保存PDF失败: {e}")
            return None

    def extract_text(self, pdf_path: str) -> str:
        """提取PDF文本内容

        优先使用pdfplumber，备选PyMuPDF
        """
        if not pdf_path or not os.path.exists(pdf_path):
            return ""

        text = ""

        # 尝试使用pdfplumber
        try:
            import pdfplumber
            text = self._extract_with_pdfplumber(pdf_path)
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            log.error(f"pdfplumber提取失败: {e}")

        # 备选：使用PyMuPDF (fitz)
        try:
            import fitz  # PyMuPDF
            text = self._extract_with_fitz(pdf_path)
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            log.error(f"PyMuPDF提取失败: {e}")

        return text

    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """使用pdfplumber提取文本"""
        import pdfplumber

        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return '\n\n'.join(text_parts)

    def _extract_with_fitz(self, pdf_path: str) -> str:
        """使用PyMuPDF提取文本"""
        import fitz

        text_parts = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_parts.append(page.get_text())
        doc.close()

        return '\n\n'.join(text_parts)

    def cleanup(self, pdf_path: str):
        """清理临时PDF文件"""
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError:
                pass

    def download_and_extract(self, url: str) -> str:
        """下载PDF并提取内容（一体化方法）"""
        pdf_path = self.download_pdf(url)
        if not pdf_path:
            return ""

        try:
            text = self.extract_text(pdf_path)
            return text
        finally:
            self.cleanup(pdf_path)