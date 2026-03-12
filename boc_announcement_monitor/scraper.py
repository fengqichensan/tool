"""网页爬取和公告解析模块"""

import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import config


class AnnouncementScraper:
    """公告页面爬取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

    def fetch_page(self, url: str = None) -> str:
        """获取公告页面HTML"""
        if url is None:
            url = config.ANNOUNCEMENT_URL

        response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text

    def parse_announcements(self, html: str) -> List[Dict]:
        """解析公告列表

        返回格式:
        [
            {
                'id': '唯一标识',
                'title': '公告标题',
                'date': '2026-03-12',
                'pdf_url': 'PDF下载链接',
                'html_url': '公告HTML页面链接'
            }
        ]
        """
        soup = BeautifulSoup(html, 'lxml')
        announcements = []

        # 查找所有链接
        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href', '')
            title = link.get_text(strip=True)

            # 匹配公告页面链接格式: ./YYYYMM/tYYYYMMDD_XXXXXXX.html
            if not title or not href:
                continue

            # 匹配相对路径的公告链接
            if not re.match(r'\./\d{6}/t\d{8}_\d+\.html', href):
                continue

            # 构建完整HTML页面URL
            html_url = urljoin(config.ANNOUNCEMENT_URL, href)

            # 从href提取日期
            date_match = re.search(r't(\d{8})_', href)
            if date_match:
                date_str = date_match.group(1)
                date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                date = datetime.now().strftime('%Y-%m-%d')

            # 生成唯一ID
            id_match = re.search(r't(\d{8})_(\d+)\.html', href)
            if id_match:
                announcement_id = f"{date}_{id_match.group(2)}"
            else:
                import hashlib
                announcement_id = f"{date}_{hashlib.md5(title.encode()).hexdigest()[:8]}"

            announcements.append({
                'id': announcement_id,
                'title': title,
                'date': date,
                'html_url': html_url,
                'pdf_url': ''  # 需要访问HTML页面才能获取
            })

        # 按日期降序排序
        announcements.sort(key=lambda x: x['date'], reverse=True)

        return announcements

    def _extract_date_near_element(self, element) -> str:
        """从元素附近提取日期"""
        # 先检查元素自身
        text = element.get_text()

        # 检查父元素和兄弟元素
        for parent in [element.parent, element.parent.parent if element.parent else None]:
            if parent:
                parent_text = parent.get_text()
                date = self._parse_date(parent_text)
                if date:
                    return date

        # 检查下一个兄弟节点
        sibling = element.find_next_sibling()
        if sibling:
            date = self._parse_date(sibling.get_text())
            if date:
                return date

        # 默认返回今天
        return datetime.now().strftime('%Y-%m-%d')

    def _parse_date(self, text: str) -> Optional[str]:
        """从文本中解析日期"""
        # 匹配多种日期格式
        patterns = [
            r'(\d{4})[年\-/\.](\d{1,2})[月\-/\.](\d{1,2})',  # 2024年03月12日 或 2024-03-12
            r'(\d{4})(\d{2})(\d{2})',  # 20240312
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                year, month, day = match.groups()
                return f"{year}-{int(month):02d}-{int(day):02d}"

        return None

    def _generate_id(self, url: str, title: str, date: str) -> str:
        """生成公告唯一ID"""
        # 使用URL中的文件名作为ID基础
        filename_match = re.search(r'/([^/]+\.pdf)', url, re.IGNORECASE)
        if filename_match:
            base_name = filename_match.group(1).replace('.pdf', '').replace('.PDF', '')
            return f"{date}_{base_name}"

        # 备选：使用日期+标题hash
        import hashlib
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
        return f"{date}_{title_hash}"

    def get_announcements(self) -> List[Dict]:
        """获取公告列表（主入口）"""
        html = self.fetch_page()
        announcements = self.parse_announcements(html)

        # 获取每个公告的PDF链接
        for ann in announcements:
            if ann.get('html_url'):
                pdf_url = self.extract_pdf_url(ann['html_url'])
                ann['pdf_url'] = pdf_url

        return announcements

    def extract_pdf_url(self, html_url: str) -> str:
        """从公告HTML页面提取PDF下载链接"""
        try:
            html = self.fetch_page(html_url)
            soup = BeautifulSoup(html, 'lxml')

            # 查找PDF链接
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '.pdf' in href.lower():
                    return urljoin(html_url, href)

            return ""
        except Exception as e:
            print(f"提取PDF链接失败: {html_url}, 错误: {e}")
            return ""