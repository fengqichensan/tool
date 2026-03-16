"""BOC announcement scraper module."""

import hashlib
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import config

log = logging.getLogger("monitor")

ANNOUNCEMENT_URL = "https://www.boc.cn/investor/ir5/"


class AnnouncementScraper:
    """BOC announcement page scraper."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

    def fetch_page(self, url: str = None) -> str:
        """Fetch announcement page HTML."""
        if url is None:
            url = ANNOUNCEMENT_URL

        response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text

    def parse_announcements(self, html: str) -> List[Dict]:
        """Parse announcement list.

        Returns format:
        [
            {
                'id': 'unique_id',
                'title': 'announcement title',
                'date': '2026-03-12',
                'pdf_url': 'PDF download link',
                'html_url': 'announcement HTML page link'
            }
        ]
        """
        soup = BeautifulSoup(html, 'lxml')
        announcements = []

        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href', '')
            title = link.get_text(strip=True)

            if not title or not href:
                continue

            if not re.match(r'\./\d{6}/t\d{8}_\d+\.html', href):
                continue

            html_url = urljoin(ANNOUNCEMENT_URL, href)

            date_match = re.search(r't(\d{8})_', href)
            if date_match:
                date_str = date_match.group(1)
                date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                date = datetime.now().strftime('%Y-%m-%d')

            id_match = re.search(r't(\d{8})_(\d+)\.html', href)
            if id_match:
                announcement_id = f"{date}_{id_match.group(2)}"
            else:
                announcement_id = f"{date}_{hashlib.md5(title.encode()).hexdigest()[:8]}"

            announcements.append({
                'id': announcement_id,
                'title': title,
                'date': date,
                'html_url': html_url,
                'pdf_url': ''
            })

        announcements.sort(key=lambda x: x['date'], reverse=True)

        return announcements

    def _extract_date_near_element(self, element) -> str:
        """Extract date from near element."""
        text = element.get_text()

        for parent in [element.parent, element.parent.parent if element.parent else None]:
            if parent:
                parent_text = parent.get_text()
                date = self._parse_date(parent_text)
                if date:
                    return date

        sibling = element.find_next_sibling()
        if sibling:
            date = self._parse_date(sibling.get_text())
            if date:
                return date

        return datetime.now().strftime('%Y-%m-%d')

    def _parse_date(self, text: str) -> Optional[str]:
        """Parse date from text."""
        patterns = [
            r'(\d{4})[年\-/\.](\d{1,2})[月\-/\.](\d{1,2})',
            r'(\d{4})(\d{2})(\d{2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                year, month, day = match.groups()
                return f"{year}-{int(month):02d}-{int(day):02d}"

        return None

    def _generate_id(self, url: str, title: str, date: str) -> str:
        """Generate unique announcement ID."""
        filename_match = re.search(r'/([^/]+\.pdf)', url, re.IGNORECASE)
        if filename_match:
            base_name = filename_match.group(1).replace('.pdf', '').replace('.PDF', '')
            return f"{date}_{base_name}"

        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        return f"{date}_{title_hash}"

    def get_announcements(self) -> List[Dict]:
        """Get announcement list (main entry)."""
        html = self.fetch_page()
        announcements = self.parse_announcements(html)

        for ann in announcements:
            if ann.get('html_url'):
                pdf_url = self.extract_pdf_url(ann['html_url'])
                ann['pdf_url'] = pdf_url

        return announcements

    def extract_pdf_url(self, html_url: str) -> str:
        """Extract PDF download link from announcement HTML page."""
        try:
            html = self.fetch_page(html_url)
            soup = BeautifulSoup(html, 'lxml')

            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '.pdf' in href.lower():
                    return urljoin(html_url, href)

            return ""
        except Exception as e:
            log.error(f"Failed to extract PDF link: {html_url}, error: {e}")
            return ""