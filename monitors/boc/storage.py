"""Sent announcement records management module."""

import json
import os
from datetime import datetime
from typing import Dict

import config


class SentRecordsStorage:
    """Sent announcement records storage manager."""

    def __init__(self):
        self.data_dir = config.DATA_DIR
        self.records_file = os.path.join(self.data_dir, "sent_records.json")
        self._ensure_data_dir()
        self.records: Dict = self._load_records()

    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_records(self) -> Dict:
        """Load sent records."""
        if os.path.exists(self.records_file):
            try:
                with open(self.records_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_records(self):
        """Save records to file."""
        with open(self.records_file, 'w', encoding='utf-8') as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    def is_sent(self, announcement_id: str) -> bool:
        """Check if announcement has been sent."""
        return announcement_id in self.records

    def mark_sent(self, announcement_id: str, title: str, date: str):
        """Mark announcement as sent."""
        self.records[announcement_id] = {
            'title': title,
            'date': date,
            'sent_at': datetime.now().isoformat()
        }
        self._save_records()

    def get_today_records(self) -> Dict:
        """Get today's sent records."""
        today = datetime.now().strftime('%Y-%m-%d')
        return {
            aid: record for aid, record in self.records.items()
            if record.get('date') == today
        }