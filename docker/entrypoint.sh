#!/bin/bash
set -e

echo "Starting BOC Announcement Monitor..."
echo "Timezone: $TZ"
echo "Current time: $(date)"

# Initialize config if not exists
if [ ! -f /app/data/schedule_config.json ]; then
    echo '{"enabled": true, "times": ["9:30", "11:30", "14:30", "16:30", "18:30"], "weekdays": [1, 2, 3, 4, 5]}' > /app/data/schedule_config.json
fi

# Initialize cron from config
python -c "
import json
import subprocess

config = json.load(open('/app/data/schedule_config.json'))
if config.get('enabled', True):
    times = config.get('times', [])
    weekdays = ','.join(str(d) for d in config.get('weekdays', [1,2,3,4,5]))
    hours_minutes = []
    for t in times:
        parts = t.split(':')
        if len(parts) == 2:
            hours_minutes.append(f'{parts[1]} {parts[0]}')
    if hours_minutes:
        time_spec = ','.join(hours_minutes)
        cron_line = f'{time_spec} * * {weekdays} cd /app && /usr/local/bin/python main.py >> /app/data/logs/cron.log 2>&1\n'
        subprocess.run(['crontab', '-'], input=cron_line.encode())
"

# Start admin web server in background
python /app/admin.py &

# Start cron in foreground
exec cron -f