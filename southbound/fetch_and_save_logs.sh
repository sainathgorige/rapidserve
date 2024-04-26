#!/bin/bash

#set -x
# Destination directory for logs
LOG_DEST="/tmp"

# Customer groups can be hardcoded for the script or passed as arguments
customer_groups=("$@")

# Function to fetch and save logs
fetch_and_save_logs() {
    local customer_group=$1
    echo "Processing customer group: $customer_group"

    log_file="${LOG_DEST}/${customer_group}.log"
    timestamp=$(date +"%Y-%m-%d %T")

    # Find containers for the current customer group and process logs
    docker ps --format '{{.Names}}' | grep "^${customer_group}" | while read container_name; do
        echo "Fetching logs from container: $container_name"
        
        # Attempt to grep 'GET' requests in the logs
        logs=$(docker logs "$container_name" | grep -i 'GET')

        if [ -n "$logs" ]; then
            # Check if the logs already exist in the file
            if ! grep -q "$timestamp $container_name" "$log_file"; then
                echo "$timestamp $container_name" >> "$log_file"
                echo "$logs" >> "$log_file"
                echo "" >> "$log_file"  # Add a newline for separation between container logs
            fi
        else
            # Check if the "No GET requests found" message already exists for the container
            if ! grep -q "$timestamp $container_name" "$log_file"; then
                echo "$timestamp $container_name" >> "$log_file"
                echo "No GET requests found in logs" >> "$log_file"
                echo "" >> "$log_file"  # Add a newline for separation between container logs
            fi
        fi
    done
}

# Loop over each customer group and fetch/save logs
for group in "${customer_groups[@]}"; do
    fetch_and_save_logs "$group"
done

echo "Log fetching complete."