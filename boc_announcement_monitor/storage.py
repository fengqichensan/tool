"""已发送公告记录管理模块"""

import json
import os
from datetime import datetime
from typing import Dict

import config


class SentRecordsStorage:
    """已发送公告记录存储管理"""

    def __init__(self):
        self.data_dir = config.DATA_DIR
        self.records_file = os.path.join(self.data_dir, config.SENT_RECORDS_FILE)
        self._ensure_data_dir()
        self.records: Dict = self._load_records()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_records(self) -> Dict:
        """加载已发送记录"""
        if os.path.exists(self.records_file):
            try:
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_records(self):
        """保存记录到文件"""
        with open(self.records_file, 'w', encoding='utf-8') as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def is_sent(self, announcement_id: str) -> bool:
        """判断公告是否已发送"""
        return announcement_id in self.records

    def mark_sent(self, announcement_id: str, title: str, date: str):
        """标记公告为已发送"""
        self.records[announcement_id] = {
            'title': title,
            'date': date,
            'sent_at': datetime.now().isoformat()
        }
        self._save_records()

    def get_today_records(self) -> Dict:
        """获取今天的发送记录"""
        today = datetime.now().strftime('%Y-%m-%d')
        return {
            aid: record for aid, record in self.records.items()
            if record.get('date') == today
        }