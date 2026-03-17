#!/bin/bash
set -e

echo "Starting Monitor System..."
echo "Timezone: $TZ"
echo "Current time: $(date)"

# Initialize BOC config if not exists
if [ ! -f /app/data/boc_config.json ]; then
    echo '{"enabled": true, "times": ["9:30", "11:30", "14:30", "16:30", "18:30"], "weekdays": [1, 2, 3, 4, 5]}' > /app/data/boc_config.json
fi

# Initialize OpenRouter config if not exists
if [ ! -f /app/data/openrouter_config.json ]; then
    echo '{"enabled": true, "models": [], "times": ["0:00"], "weekdays": [0, 1, 2, 3, 4, 5, 6]}' > /app/data/openrouter_config.json
fi

# Initialize cron from config
python -c "
import json
import subprocess

# Load BOC config
boc_config = json.load(open('/app/data/boc_config.json'))
openrouter_config = json.load(open('/app/data/openrouter_config.json'))

cron_lines = []

# BOC cron entries
if boc_config.get('enabled', True):
    times = boc_config.get('times', [])
    weekdays = ','.join(str(d) for d in boc_config.get('weekdays', [1,2,3,4,5]))

    minute_hours = {}
    for t in times:
        parts = t.split(':')
        if len(parts) == 2:
            minute = parts[1]
            hour = int(parts[0])
            if minute not in minute_hours:
                minute_hours[minute] = []
            if hour not in minute_hours[minute]:
                minute_hours[minute].append(hour)

    for minute, hours in minute_hours.items():
        hours_str = ','.join(str(h) for h in sorted(hours))
        cron_lines.append(f'{minute} {hours_str} * * {weekdays} cd /app && /usr/local/bin/python -m monitors.boc.main >> /app/data/logs/cron.log 2>&1')

# OpenRouter cron entries
if openrouter_config.get('enabled', True):
    times = openrouter_config.get('times', ['0:00'])
    weekdays = ','.join(str(d) for d in openrouter_config.get('weekdays', [0,1,2,3,4,5,6]))

    minute_hours = {}
    for t in times:
        parts = t.split(':')
        if len(parts) == 2:
            minute = parts[1]
            hour = int(parts[0])
            if minute not in minute_hours:
                minute_hours[minute] = []
            if hour not in minute_hours[minute]:
                minute_hours[minute].append(hour)

    for minute, hours in minute_hours.items():
        hours_str = ','.join(str(h) for h in sorted(hours))
        cron_lines.append(f'{minute} {hours_str} * * {weekdays} cd /app && /usr/local/bin/python -m monitors.openrouter.main >> /app/data/logs/cron.log 2>&1')

if cron_lines:
    cron_content = chr(10).join(cron_lines) + chr(10)
    subprocess.run(['crontab', '-'], input=cron_content.encode())
"

# Start admin web server in background
python /app/admin.py &

# Start cron in foreground
exec cron -f