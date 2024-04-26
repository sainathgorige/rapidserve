#!/bin/bash

# Determine the correct container name based on the host IP
HOST_IP=$(hostname -I | awk '{print $1}')
CONTAINER_NAME=""

case "$HOST_IP" in
    "192.168.38.8")
        CONTAINER_NAME="dns_cont_host1"
        ;;
    "192.168.38.9")
        CONTAINER_NAME="dns_cont_host2"
        ;;
    *)
        echo "Unknown host IP, script will not run."
        exit 1
        ;;
esac

# Path to file where the last run timestamp is stored
LAST_RUN_FILE="/tmp/last_run.txt"

# Fetch current time minus 5 minutes as the start time for logs, in the format docker logs expects
if [ -f "$LAST_RUN_FILE" ]; then
    # Read the last run time from the file
    LAST_RUN=$(cat "$LAST_RUN_FILE")
else
    # Default to current time minus 5 minutes if no last run file exists
    LAST_RUN=$(date --date='5 minutes ago' '+%Y-%m-%dT%H:%M:%S')
fi

# Update last run file with current time for next run
date '+%Y-%m-%dT%H:%M:%S' > "$LAST_RUN_FILE"

# Directory where logs for each tenant will be stored
OUTPUT_DIR="/tmp"
mkdir -p "$OUTPUT_DIR"

# Fetch logs from the Docker container for the last 5 minutes using docker logs command
docker logs "$CONTAINER_NAME" --since "$LAST_RUN" | grep 'cdn.com' | while read line; do
    # Extract the tenant name from the log entry
    tenant=$(echo "$line" | grep -oP '(?<=\()\w+(?=.cdn.com)')

    # Check if the tenant name was found
    if [ ! -z "$tenant" ]; then
        # Output to a separate log file for each tenant
        echo "$line" >> "${OUTPUT_DIR}/${tenant}_dns_queries.log"
    fi
done

