#!/usr/bin/env python3
"""Shared admin interface - Web management page for controlling scheduled tasks."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

DATA_DIR = "/app/data"
PYTHON_PATH = "/usr/local/bin/python"

# BOC Monitor Config
BOC_CONFIG_FILE = f"{DATA_DIR}/boc_config.json"
BOC_LOG_FILE = f"{DATA_DIR}/logs/cron.log"

# OpenRouter Monitor Config
OPENROUTER_CONFIG_FILE = f"{DATA_DIR}/openrouter_config.json"

DEFAULT_BOC_CONFIG = {
    "enabled": True,
    "times": ["9:30", "11:30", "14:30", "16:30", "18:30"],
    "weekdays": [1, 2, 3, 4, 5],
}

DEFAULT_OPENROUTER_CONFIG = {
    "enabled": True,
    "models": [],
    "times": ["0:00"],
    "weekdays": [0, 1, 2, 3, 4, 5, 6],
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>监控系统 - 管理界面</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa; min-height: 100vh; padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #1a1a2e; margin-bottom: 20px; font-size: 24px; }
        h2 { color: #1a1a2e; margin-bottom: 16px; font-size: 18px; border-bottom: 2px solid #007bff; padding-bottom: 8px; }
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
        .time-tag .remove { cursor: pointer; color: #dc3545; font-weight: bold; }
        .model-tag {
            background: #e3f2fd; padding: 6px 12px; border-radius: 6px;
            font-size: 13px; display: flex; align-items: center; gap: 6px;
            font-family: monospace;
        }
        .model-tag .remove { cursor: pointer; color: #dc3545; font-weight: bold; }
        .add-time, .add-model { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
        .add-time input, .add-model input {
            padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;
            font-size: 14px; flex: 1; min-width: 150px;
        }
        .weekdays { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
        .weekday {
            width: 40px; height: 40px; border-radius: 50%; border: 2px solid #ddd;
            display: flex; align-items: center; justify-content: center;
            cursor: pointer; font-size: 14px; transition: all 0.2s;
        }
        .weekday.active { background: #007bff; border-color: #007bff; color: white; }
        .weekday.inactive { background: #f8f9fa; color: #6c757d; }
        .logs {
            background: #1a1a2e; color: #00ff00; padding: 16px; border-radius: 8px;
            font-family: monospace; font-size: 12px; max-height: 300px;
            overflow-y: auto; white-space: pre-wrap;
        }
        .info { color: #6c757d; font-size: 14px; margin-top: 8px; }
        .actions { display: flex; gap: 12px; flex-wrap: wrap; }
        .schedule-input {
            padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;
            font-size: 14px; font-family: monospace; width: 150px;
        }
        .section-divider {
            height: 2px; background: #e9ecef; margin: 30px 0;
        }
        .models-container { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
        .price-info {
            background: #f8f9fa; padding: 12px; border-radius: 6px;
            font-size: 13px; margin-top: 12px;
        }
        .price-info code { background: #e9ecef; padding: 2px 6px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>监控系统 - 管理界面</h1>
        <p class="info">当前时间: {{ now }}</p>

        <!-- BOC 公告监控 -->
        <h2>BOC 公告监控</h2>
        <div class="card">
            <div class="card-title">任务状态</div>
            <div class="status-row">
                <span class="status-badge {{ 'status-enabled' if boc.enabled else 'status-disabled' }}">
                    {{ '运行中' if boc.enabled else '已停止' }}
                </span>
            </div>
            <div class="actions">
                {% if boc.enabled %}
                <button class="btn btn-danger" onclick="toggleBoc(false)">停止定时任务</button>
                {% else %}
                <button class="btn btn-success" onclick="toggleBoc(true)">启动定时任务</button>
                {% endif %}
                <button class="btn btn-run" onclick="runBoc()">立即执行一次</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title">执行时间</div>
            <div class="times-container">
                {% for time in boc.times %}
                <span class="time-tag">
                    {{ time }}
                    <span class="remove" onclick="removeBocTime('{{ time }}')">&times;</span>
                </span>
                {% endfor %}
            </div>
            <div class="add-time">
                <input type="time" id="newBocTime" step="60">
                <button class="btn btn-primary" onclick="addBocTime()">添加时间</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title">执行日期</div>
            <div class="weekdays">
                {% for day in weekdays %}
                <div class="weekday {{ 'active' if day.id in boc.weekdays else 'inactive' }}"
                     onclick="toggleBocWeekday({{ day.id }})">
                    {{ day.name }}
                </div>
                {% endfor %}
            </div>
            <p class="info">点击切换选中状态，蓝色表示选中</p>
        </div>

        <div class="section-divider"></div>

        <!-- OpenRouter 价格监控 -->
        <h2>OpenRouter 价格监控</h2>
        <div class="card">
            <div class="card-title">任务状态</div>
            <div class="status-row">
                <span class="status-badge {{ 'status-enabled' if openrouter.enabled else 'status-disabled' }}">
                    {{ '运行中' if openrouter.enabled else '已停止' }}
                </span>
            </div>
            <div class="actions">
                {% if openrouter.enabled %}
                <button class="btn btn-danger" onclick="toggleOpenRouter(false)">停止定时任务</button>
                {% else %}
                <button class="btn btn-success" onclick="toggleOpenRouter(true)">启动定时任务</button>
                {% endif %}
                <button class="btn btn-run" onclick="runOpenRouter()">立即执行一次</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title">监控模型</div>
            <div class="models-container">
                {% for model in openrouter.models %}
                <span class="model-tag">
                    {{ model }}
                    <span class="remove" onclick="removeModel('{{ model }}')">&times;</span>
                </span>
                {% endfor %}
            </div>
            <div class="add-model">
                <input type="text" id="newModel" placeholder="例如: openai/gpt-4">
                <button class="btn btn-primary" onclick="addModel()">添加模型</button>
            </div>
            <p class="info">当监控的模型价格不为0时，会发送Telegram通知</p>
        </div>

        <div class="card">
            <div class="card-title">执行时间</div>
            <div class="times-container">
                {% for time in openrouter.times %}
                <span class="time-tag">
                    {{ time }}
                    <span class="remove" onclick="removeOpenRouterTime('{{ time }}')">&times;</span>
                </span>
                {% endfor %}
            </div>
            <div class="add-time">
                <input type="time" id="newOpenRouterTime" step="60">
                <button class="btn btn-primary" onclick="addOpenRouterTime()">添加时间</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title">执行日期</div>
            <div class="weekdays">
                {% for day in weekdays %}
                <div class="weekday {{ 'active' if day.id in openrouter.weekdays else 'inactive' }}"
                     onclick="toggleOpenRouterWeekday({{ day.id }})">
                    {{ day.name }}
                </div>
                {% endfor %}
            </div>
            <p class="info">点击切换选中状态，蓝色表示选中</p>
        </div>

        <div class="section-divider"></div>

        <!-- 日志 -->
        <div class="card">
            <div class="card-title">最近日志</div>
            <div class="logs">{{ logs }}</div>
        </div>
    </div>

    <script>
        // BOC Functions
        function toggleBoc(enabled) {
            fetch('/api/boc/enabled', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: enabled})
            }).then(() => location.reload());
        }

        function runBoc() {
            fetch('/api/boc/run', {method: 'POST'})
                .then(r => r.json())
                .then(d => alert(d.message || d.error))
                .then(() => location.reload());
        }

        function addBocTime() {
            const time = document.getElementById('newBocTime').value;
            if (!time) return alert('请选择时间');
            fetch('/api/boc/times', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({time: time})
            }).then(() => location.reload());
        }

        function removeBocTime(time) {
            fetch('/api/boc/times', {
                method: 'DELETE',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({time: time})
            }).then(() => location.reload());
        }

        function toggleBocWeekday(dayId) {
            fetch('/api/boc/weekdays', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({weekday: dayId})
            }).then(() => location.reload());
        }

        // OpenRouter Functions
        function toggleOpenRouter(enabled) {
            fetch('/api/openrouter/enabled', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({enabled: enabled})
            }).then(() => location.reload());
        }

        function runOpenRouter() {
            fetch('/api/openrouter/run', {method: 'POST'})
                .then(r => r.json())
                .then(d => alert(d.message || d.error))
                .then(() => location.reload());
        }

        function addModel() {
            const model = document.getElementById('newModel').value.trim();
            if (!model) return alert('请输入模型ID');
            fetch('/api/openrouter/models', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model: model})
            }).then(() => location.reload());
        }

        function removeModel(model) {
            fetch('/api/openrouter/models', {
                method: 'DELETE',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model: model})
            }).then(() => location.reload());
        }

        function addOpenRouterTime() {
            const time = document.getElementById('newOpenRouterTime').value;
            if (!time) return alert('请选择时间');
            fetch('/api/openrouter/times', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({time: time})
            }).then(() => location.reload());
        }

        function removeOpenRouterTime(time) {
            fetch('/api/openrouter/times', {
                method: 'DELETE',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({time: time})
            }).then(() => location.reload());
        }

        function toggleOpenRouterWeekday(dayId) {
            fetch('/api/openrouter/weekdays', {
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
    """Normalize time format by removing leading zeros from hour."""
    parts = time_str.split(":")
    if len(parts) == 2:
        hour = int(parts[0])
        minute = parts[1]
        return f"{hour}:{minute}"
    return time_str


def load_boc_config() -> dict:
    """Load BOC schedule configuration."""
    config_path = Path(BOC_CONFIG_FILE)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_BOC_CONFIG.copy()


def save_boc_config(config: dict) -> None:
    """Save BOC configuration."""
    config_path = Path(BOC_CONFIG_FILE)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_openrouter_config() -> dict:
    """Load OpenRouter configuration."""
    config_path = Path(OPENROUTER_CONFIG_FILE)
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_OPENROUTER_CONFIG.copy()


def save_openrouter_config(config: dict) -> None:
    """Save OpenRouter configuration."""
    config_path = Path(OPENROUTER_CONFIG_FILE)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def update_crontab() -> None:
    """Update crontab with all monitors' schedules."""
    boc_config = load_boc_config()
    openrouter_config = load_openrouter_config()

    cron_lines = []

    # BOC cron entries
    if boc_config.get("enabled", True):
        times = boc_config.get("times", [])
        weekdays = ",".join(str(d) for d in boc_config.get("weekdays", [1, 2, 3, 4, 5]))

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

        for minute, hours in minute_hours.items():
            hours_str = ",".join(str(h) for h in sorted(hours))
            cron_lines.append(
                f"{minute} {hours_str} * * {weekdays} cd /app && {PYTHON_PATH} -m monitors.boc.main >> {BOC_LOG_FILE} 2>&1"
            )

    # OpenRouter cron entries
    if openrouter_config.get("enabled", True):
        times = openrouter_config.get("times", [])
        weekdays = ",".join(str(d) for d in openrouter_config.get("weekdays", [0, 1, 2, 3, 4, 5, 6]))

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

        for minute, hours in minute_hours.items():
            hours_str = ",".join(str(h) for h in sorted(hours))
            cron_lines.append(
                f"{minute} {hours_str} * * {weekdays} cd /app && {PYTHON_PATH} -m monitors.openrouter.main >> {BOC_LOG_FILE} 2>&1"
            )

    if not cron_lines:
        result = subprocess.run(["crontab", "-r"], capture_output=True)
        log.info(f"Removed crontab, returncode={result.returncode}")
        return

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
    log_path = Path(BOC_LOG_FILE)
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
    boc = load_boc_config()
    openrouter = load_openrouter_config()
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
        boc=boc,
        openrouter=openrouter,
        weekdays=weekdays,
        logs=get_logs(),
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


# BOC API Routes
@app.route("/api/boc/enabled", methods=["POST"])
def set_boc_enabled():
    data = request.get_json()
    config = load_boc_config()
    config["enabled"] = data.get("enabled", True)
    save_boc_config(config)
    update_crontab()
    return jsonify({"success": True})


@app.route("/api/boc/times", methods=["POST"])
def add_boc_schedule_time():
    data = request.get_json()
    time_str = normalize_time(data.get("time", ""))
    config = load_boc_config()
    if time_str and time_str not in config["times"]:
        config["times"].append(time_str)
        config["times"].sort(key=lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1]))
        save_boc_config(config)
        update_crontab()
    return jsonify({"success": True})


@app.route("/api/boc/times", methods=["DELETE"])
def remove_boc_schedule_time():
    data = request.get_json()
    time_str = normalize_time(data.get("time", ""))
    config = load_boc_config()
    if time_str in config["times"]:
        config["times"].remove(time_str)
        save_boc_config(config)
        update_crontab()
    return jsonify({"success": True})


@app.route("/api/boc/weekdays", methods=["POST"])
def toggle_boc_weekday():
    data = request.get_json()
    day_id = data.get("weekday")
    config = load_boc_config()
    if day_id in config["weekdays"]:
        config["weekdays"].remove(day_id)
    else:
        config["weekdays"].append(day_id)
        config["weekdays"].sort()
    save_boc_config(config)
    update_crontab()
    return jsonify({"success": True})


@app.route("/api/boc/run", methods=["POST"])
def run_boc_now():
    try:
        result = subprocess.run(
            [PYTHON_PATH, "-m", "monitors.boc.main"],
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


# OpenRouter API Routes
@app.route("/api/openrouter/enabled", methods=["POST"])
def set_openrouter_enabled():
    data = request.get_json()
    config = load_openrouter_config()
    config["enabled"] = data.get("enabled", True)
    save_openrouter_config(config)
    update_crontab()
    return jsonify({"success": True})


@app.route("/api/openrouter/models", methods=["POST"])
def add_openrouter_model():
    data = request.get_json()
    model = data.get("model", "").strip()
    config = load_openrouter_config()
    if model and model not in config["models"]:
        config["models"].append(model)
        save_openrouter_config(config)
    return jsonify({"success": True})


@app.route("/api/openrouter/models", methods=["DELETE"])
def remove_openrouter_model():
    data = request.get_json()
    model = data.get("model", "").strip()
    config = load_openrouter_config()
    if model in config["models"]:
        config["models"].remove(model)
        save_openrouter_config(config)
    return jsonify({"success": True})


@app.route("/api/openrouter/times", methods=["POST"])
def add_openrouter_schedule_time():
    data = request.get_json()
    time_str = normalize_time(data.get("time", ""))
    config = load_openrouter_config()
    if time_str and time_str not in config.get("times", []):
        if "times" not in config:
            config["times"] = []
        config["times"].append(time_str)
        config["times"].sort(key=lambda t: int(t.split(":")[0]) * 60 + int(t.split(":")[1]))
        save_openrouter_config(config)
        update_crontab()
    return jsonify({"success": True})


@app.route("/api/openrouter/times", methods=["DELETE"])
def remove_openrouter_schedule_time():
    data = request.get_json()
    time_str = normalize_time(data.get("time", ""))
    config = load_openrouter_config()
    if time_str in config.get("times", []):
        config["times"].remove(time_str)
        save_openrouter_config(config)
        update_crontab()
    return jsonify({"success": True})


@app.route("/api/openrouter/weekdays", methods=["POST"])
def toggle_openrouter_weekday():
    data = request.get_json()
    day_id = data.get("weekday")
    config = load_openrouter_config()
    if "weekdays" not in config:
        config["weekdays"] = [0, 1, 2, 3, 4, 5, 6]
    if day_id in config["weekdays"]:
        config["weekdays"].remove(day_id)
    else:
        config["weekdays"].append(day_id)
        config["weekdays"].sort()
    save_openrouter_config(config)
    update_crontab()
    return jsonify({"success": True})


@app.route("/api/openrouter/run", methods=["POST"])
def run_openrouter_now():
    try:
        result = subprocess.run(
            [PYTHON_PATH, "-m", "monitors.openrouter.main"],
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
        "boc_config": load_boc_config(),
        "openrouter_config": load_openrouter_config()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)