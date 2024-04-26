#!/bin/bash

# Variables
MONITORED_DIR="/var/www/html/"
PLAYBOOK_PATH="/root/origin_server.yaml"
LOG_FILE="/var/log/monitoring.log"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Start monitoring
log "Monitoring started for $MONITORED_DIR"

inotifywait -m -e modify,move,create,delete --format '%w%f' -- "$MONITORED_DIR" | while read FILE; do
    # Using grep to check if the file matches the numeric pattern
    if echo "$FILE" | grep -q -E '/var/www/html/[0-9]+$'; then
        log "Change detected in $FILE, executing playbook..."
        ansible-playbook "$PLAYBOOK_PATH" -i /root/dynamic_inventory.ini >> "$LOG_FILE" 2>&1
        log "Playbook execution completed."
    fi
done
