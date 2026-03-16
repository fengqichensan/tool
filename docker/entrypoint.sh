#!/bin/bash
set -e

echo "Starting BOC Announcement Monitor..."
echo "Timezone: $TZ"
echo "Current time: $(date)"

# Initialize config if not exists
if [ ! -f /app/data/schedule_config.json ]; then
    echo '{"enabled": true, "times": ["9:30", "11:30", "14:30", "16:30", "18:30"], "weekdays": [1, 2, 3, 4, 5]}' > /app/data/schedule_config.json
fi

# Start admin web server in background
python /app/admin.py &

# Start cron in foreground
exec cron -f