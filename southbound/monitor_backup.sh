#!/bin/bash

set -x
log_with_date() {
    while IFS= read -r line; do
        echo "$(date +'%Y-%m-%d %H:%M:%S') $line" 
    done
}

# Check if a region was passed as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <region_name>" | log_with_date
    exit 1
fi

# The region or VPC base name
vpc_name="$1"
container_base_name="${vpc_name}_container"  # Using VPC name for container base

# Set the minimum number of containers.
min_containers=1
# CPU usage threshold for scaling up or down.
cpu_threshold=10

# Function to get the current number of running containers.
get_running_containers() {
    docker ps --filter "name=${container_base_name}" --format "{{.Names}}" | wc -l
}

# Function to check if CPU usage for a specific container is above the threshold.
check_cpu_usage() {
    local container_name="$1"
    docker stats --no-stream --format "{{.CPUPerc}}" $container_name | tr -d '%' | awk '{print $1}'
}

# Function to scale up containers
scale_up() {
    local num_containers=$(get_running_containers)
    local next_container_num=$((num_containers + 1))  # Increment to the next container number
    local container_ip=$(python3 /home/vmadm/demo/RapidServe/southbound/get_container_ip.py ${vpc_name^^})
    echo "Scaling up: Adding 1 container, total will be ${container_base_name}${next_container_num}" | log_with_date
    ansible-playbook /home/vmadm/demo/RapidServe/southbound/deploy_con.yaml --extra-vars "{\"container_num\": \"$next_container_num\", \"subnets\": [\"${vpc_name^^}_S1\"], \"vpc_name\": \"${vpc_name}\", \"container_ip\": \"${container_ip}\"}"
}

# Function to scale down containers
scale_down() {
    local num_containers=$(get_running_containers)
    if [ "$num_containers" -gt "$min_containers" ]; then
        local last_container_num=$num_containers
        echo "Scaling down: Removing container number ${container_base_name}${last_container_num}" | log_with_date
        ansible-playbook /home/vmadm/demo/RapidServe/southbound/destroy_con.yaml --extra-vars "container_num=$last_container_num, bridge_name=${vpc_name}_S1 vpc_name=${vpc_name}"
    fi
}

# Check each container and count how many are above the CPU threshold.
containers_above_threshold=0
running_containers=$(get_running_containers)

for ((i=1; i<=running_containers; i++)); do
    container_name="${container_base_name}${i}"
    if docker ps --format "{{.Names}}" | grep -q $container_name; then
        cpu_usage=$(check_cpu_usage "$container_name")
        echo $cpu_usage

        if (( $(echo "$cpu_usage > $cpu_threshold" | bc -l) )); then
            ((containers_above_threshold++))
            echo "container is more than threshold"
            echo $containers_above_threshold
        fi
    fi
done

# Decide on scaling action based on the current state.
if ((containers_above_threshold >= min_containers)); then
    scale_up
elif ((running_containers > min_containers && containers_above_threshold == 0)); then
    scale_down
else
    echo "No scaling required." | log_with_date
fi
