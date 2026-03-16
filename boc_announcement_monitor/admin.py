#!/usr/bin/env python3
"""管理界面 - Web管理页面用于控制定时任务"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

CONFIG_FILE = "/app/data/schedule_config.json"
LOG_FILE = "/app/data/logs/cron.log"
PYTHON_PATH = "/usr/local/bin/python"

DEFAULT_SCHEDULE = {
    "enabled": True,
    "times": ["9:30", "11:30", "14:30", "16:30", "18:30"],
    "weekdays": [1, 2, 3, 4, 5],
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BOC公告监控 - 管理界面</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa; min-height: 100vh; padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #1a1a2e; margin-bottom: 20px; font-size: 24px; }
        .card {
            background: white; border-radius: 12px; padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px;
        }
        .card-title { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 16px; }
        .status-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
        .status-badge {
            padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: 500;
        }
        .status-enabled { background: #d4edda; color: #155724; }
        .status-disabled { background: #f8d7da; color: #721c24; }
        .btn {
            padding: 10px 20px; border: none; border-radius: 8px;
            cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.2s;
        }
        .btn-primary { background: #007bff; color: white; }
        .btn-primary:hover { background: #0056b3; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-danger:hover { background: #c82333; }
        .btn-success { background: #28a745; color: white; }
        .btn-success:hover { background: #1e7e34; }
        .btn-run { background: #17a2b8; color: white; }
        .btn-run:hover { background: #138496; }
        .times-container { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
        .time-tag {
            background: #e9ecef; padding: 6px 12px; border-radius: 6px;
            font-size: 14px; display: flex; align-items: center; gap: 6px;
        }
        .time-tag .remove {
            cursor: pointer; color: #dc3545; font-weight: bold;
        }
        .add-time { display: flex; gap: 8px; margin-bottom: 16px; }
        .add-time input {
            padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;
            font-size: 14px; width: 120px;
        }
        .weekdays { display: flex; gap: 8px; margin-bottom: 16px; }
        .weekday {
            width: 40px; height: 40px; border-radius: 50%; border: 2px solid #ddd;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; font-size: 14px; transition: all 0.2s;
        }
        .weekday.active { background: #007bff; border-color: #007bff; color: white; }
        .weekday.inactive { background: #f8f9fa; color: #6c757d; }
        .logs { background: #1a1a2e; color: #00ff00; padding: 16px; border-radius: 8px;
                font-family: monospace; font-size: 12px; max-height: 300px;
                overflow-y: auto; white-space: pre-wrap; }
        .info { color: #6c757d; font-size: 14px; margin-top: 8px; }
        .actions { display: flex; gap: 12px; flex-wrap: wrap; }
    </style>
</head>
<body>
    <div class="container">
        <h1>BOC公告监控 - 管理界面</h1>

        <div class="card">
            <div class="card-title">任务状态</div>
            <div class="status-row">
                <span class="status-badge {{ 'status-enabled' if config.enabled else 'status-disabled' }}">
                    {{ '运行中' if config.enabled else '已停止' }}
                </span>
                <span class="info">当前时间: {{ now }}</span>
            </div>
            <div class="actions">
                {% if config.enabled %}
                <button class="btn btn-danger" onclick="toggleSchedule(false)">停止定时任务</button>
                {% else %}
                <button class="btn btn-success" onclick="toggleSchedule(true)">启动定时任务</button>
                {% endif %}
                <button class="btn btn-run" onclick="runNow()">立即执行一次</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title">执行时间 (工作日)</div>
            <div class="times-container">
                {% for time in config.times %}
                <span class="time-tag">
                    {{ time }}
                    <span class="remove" onclick="removeTime('{{ time }}')">×</span>
                </span>
                {% endfor %}
            </div>
            <div class="add-time">
                <input type="time" id="newTime" step="60">
                <button class="btn btn-primary" onclick="addTime()">添加时间</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title">执行日期</div>
            <div class="weekdays">
                {% for day in weekdays %}
                <div class="weekday {{ 'active' if day.id in config.weekdays else 'inactive' }}"
                     onclick="toggleWeekday({{ day.id }})">
                    {{ day.name }}
                </div>
                {% endfor %}
            </div>
            <p class="info">点击切换选中状态，蓝色表示选中</p>
        </div>

        <div class="card">
            <div class="card-title">最近日志</div>
            <div class="logs">{{ logs }}</div>
        </div>
    </div>

    <script>
        function toggleSchedule(enabled) {
            fetch('/api/schedule/enabled', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: enabled})
            }).then(() => location.reload());
        }

        function runNow() {
            fetch('/api/run', {method: 'POST'})
                .then(r => r.json())
                .then(d => alert(d.message || d.error))
                .then(() => location.reload());
        }

        function addTime() {
            const time = document.getElementById('newTime').value;
            if (!time) return alert('请选择时间');
            fetch('/api/schedule/times', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({time: time})
            }).then(() => location.reload());
        }

        function removeTime(time) {
            fetch('/api/schedule/times', {
                method: 'DELETE',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({time: time})
            }).then(() => location.reload());
        }

        function toggleWeekday(dayId) {
            fetch('/api/schedule/weekdays', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({weekday: dayId})
            }).then(() => location.reload());
        }
    </script>
</body>
</html>
"""


def normalize_time(time_str: str) -> str:
    """Normalize time format by removing leading zeros from hour.

    Args:
        time_str: Time string in "HH:MM" format

    Returns:
        Normalized time string like "9:30" instead of "09:30"
    """
    parts = time_str.split(":")
    if len(parts) == 2:
        hour = int(parts[0])
        minute = parts[1]
        return f"{hour}:{minute}"
    return time_str


def load_config() -> dict:
    """Load schedule configuration from file."""
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_SCHEDULE.copy()


def save_config(config: dict) -> None:
    """Save schedule configuration to file."""
    config_path = Path(CONFIG_FILE)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def update_cron(config: dict) -> None:
    """Update crontab based on configuration."""
    if not config["enabled"]:
        result = subprocess.run(["crontab", "-r"], capture_output=True)
        log.info(f"Removed crontab, returncode={result.returncode}")
        return

    times = config["times"]
    weekdays = ",".join(str(d) for d in config["weekdays"])

    # Group hours by minute for correct cron syntax
    # e.g., "9:30" and "11:30" -> minute 30, hours [9, 11] -> "30 9,11"
    minute_hours: dict[str, list[int]] = {}
    for t in times:
        parts = t.split(":")
        if len(parts) == 2:
            minute = parts[1]
            hour = int(parts[0])
            if minute not in minute_hours:
                minute_hours[minute] = []
            if hour not in minute_hours[minute]:
                minute_hours[minute].append(hour)

    if not minute_hours:
        result = subprocess.run(["crontab", "-r"], capture_output=True)
        log.info(f"Removed crontab (no times), returncode={result.returncode}")
        return

    cron_lines = []
    for minute, hours in minute_hours.items():
        hours_str = ",".join(str(h) for h in sorted(hours))
        cron_lines.append(
            f"{minute} {hours_str} * * {weekdays} cd /app && {PYTHON_PATH} main.py >> /app/data/logs/cron.log 2>&1"
        )

    cron_content = "\n".join(cron_lines) + "\n"
    log.info(f"Setting crontab:\n{cron_content}")

    result = subprocess.run(
        ["crontab", "-"],
        input=cron_content.encode(),
        capture_output=True,
    )

    if result.returncode != 0:
        log.error(f"crontab command failed: {result.stderr.decode()}")
    else:
        log.info("crontab updated successfully")


def get_logs() -> str:
    """Read recent logs."""
    log_path = Path(LOG_FILE)
    if not log_path.exists():
        return "暂无日志"
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[-100:])
    except Exception:
        return "读取日志失败"


@app.route("/")
def index():
    config = load_config()
    weekdays = [
        {"id": 0, "name": "日"},
        {"id": 1, "name": "一"},
        {"id": 2, "name": "二"},
        {"id": 3, "name": "三"},
        {"id": 4, "name": "四"},
        {"id": 5, "name": "五"},
        {"id": 6, "name": "六"},
    ]
    return render_template_string(
        HTML_TEMPLATE,
        config=config,
        weekdays=weekdays,
        logs=get_logs(),
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.route("/api/schedule/enabled", methods=["POST"])
def set_enabled():
    data = request.get_json()
    config = load_config()
    config["enabled"] = data.get("enabled", True)
    save_config(config)
    update_cron(config)
    return jsonify({"success": True})


@app.route("/api/schedule/times", methods=["POST"])
def add_schedule_time():
    data = request.get_json()
    time_str = normalize_time(data.get("time", ""))
    config = load_config()
    if time_str and time_str not in config["times"]:
        config["times"].append(time_str)
        config["times"].sort(key=lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1]))
        save_config(config)
        update_cron(config)
    return jsonify({"success": True})


@app.route("/api/schedule/times", methods=["DELETE"])
def remove_schedule_time():
    data = request.get_json()
    time_str = normalize_time(data.get("time", ""))
    config = load_config()
    if time_str in config["times"]:
        config["times"].remove(time_str)
        save_config(config)
        update_cron(config)
    return jsonify({"success": True})


@app.route("/api/schedule/weekdays", methods=["POST"])
def toggle_weekday():
    data = request.get_json()
    day_id = data.get("weekday")
    config = load_config()
    if day_id in config["weekdays"]:
        config["weekdays"].remove(day_id)
    else:
        config["weekdays"].append(day_id)
        config["weekdays"].sort()
    save_config(config)
    update_cron(config)
    return jsonify({"success": True})


@app.route("/api/run", methods=["POST"])
def run_now():
    try:
        result = subprocess.run(
            [PYTHON_PATH, "/app/main.py"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return jsonify({"message": "执行成功", "output": result.stdout})
        return jsonify({"error": f"执行失败: {result.stderr}"})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "执行超时"})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/debug/crontab", methods=["GET"])
def debug_crontab():
    """Debug endpoint to check current crontab status."""
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return jsonify({
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "config": load_config()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)