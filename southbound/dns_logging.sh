#!/bin/bash

# Define the containers and their respective VMs
declare -A containers=( ["dns_cont_host1"]="192.168.38.8" ["dns_cont_host2"]="192.168.38.9" )

# Loop through each container
for container in "${!containers[@]}"; do
    echo "Starting to monitor logs for container $container on host ${containers[$container]}"
    
    # Follow the logs of each container using docker command executed on respective VMs via SSH (assuming you have SSH access and permissions set up)
    ssh vmadm@${containers[$container]} "docker logs --follow $container" |
    while read line; do
        # Extract the tenant name from the log entry
        tenant=$(echo "$line" | grep -oP '(?<=\()\w+(?=.cdn.com)')

        # Check if the tenant name was found
        if [ ! -z "$tenant" ]; then
            # Output to a separate log file for each tenant
            echo "$line" >> "/tmp/${tenant}_dns_queries.log"
        fi
    done
done
