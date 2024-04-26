#!/bin/bash

#set -x

# Function to log with timestamp
log_with_date() {
    while IFS= read -r line; do
        echo "$(date +'%Y-%m-%d %H:%M:%S') $line" 
    done
}

# Exit if no region name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <region_name>" | log_with_date
    exit 1
fi

# Convert region name to uppercase
vpc_name="${1}"
SUBNET_NAME="${vpc_name}_S1"
container_base_name="${vpc_name}_container"

# Minimum number of containers and CPU threshold for scaling
min_containers=1
max_containers=4
cpu_threshold=10


# Path to the file that tracks IP assignments
# ip_file="/home/vmadm/demo/RapidServe/southbound/${vpc_name}_ips.txt"

# # Initializes or updates the IP file with the next available IP
# initialize_ip() {
#     local base_ip=$(python3 /home/vmadm/demo/RapidServe/southbound/get_container_ip.py ${vpc_name^^})
#     local last_octet=$(echo $base_ip | awk -F '.' '{print $4}')
#     local base="$(echo $base_ip | cut -d'.' -f1-3)"
    
#     if [[ ! -f $ip_file ]]; then
#         echo "$base.$((last_octet + 1))" > $ip_file
#     fi
# }

# # Retrieves the next available IP
# get_next_ip() {
#     local last_ip=$(tail -n 1 $ip_file)
#     local last_octet=$(echo $last_ip | awk -F '.' '{print $4}')
#     local base="$(echo $last_ip | cut -d'.' -f1-3)"
#     local next_ip="$base.$((last_octet + 1))"
#     echo $next_ip >> $ip_file
#     echo $next_ip
# }

# # Initialize IP tracking
# initialize_ip

# Get the current number of running containers
get_running_containers() {
    docker ps --filter "name=${container_base_name}" --format "{{.Names}}" | wc -l
}

# Check CPU usage of a specific container
check_cpu_usage() {
    local container_name="$1"
    docker stats --no-stream --format "{{.CPUPerc}}" $container_name | tr -d '%' | awk '{print $1}'
}

# Scale up the number of containers
scale_up() {
    local num_containers=$(get_running_containers)
    if [ "$num_containers" -lt "$max_containers" ]; then
        local next_container_num=$((num_containers + 1))
    #    local container_ip=$(get_next_ip)
        local container_name="${container_base_name}${next_container_num}"
        echo "Scaling up: Adding container ${container_name}" | log_with_date
        ansible-playbook -i /home/vmadm/demo/RapidServe/southbound/localhost.ini /home/vmadm/demo/RapidServe/southbound/deploy_con.yaml --extra-vars "{\"container_name\": \"$container_name\", \"subnets\": [\"${vpc_name}_S1\"], \"vpc_name\": \"${vpc_name}\"}"
    else
        echo "Maximum container limit reached. Cannot scale up further." | log_with_date
    fi
}
# Scale down the number of containers
scale_down() {
    local container_nums=($(docker ps --filter "name=${container_base_name}" --format "{{.Names}}" | sed -e "s/${container_base_name}\([0-9]*\)/\1/" | sort -nr))
    local num_containers=${#container_nums[@]}
    if [ "$num_containers" -gt "$min_containers" ]; then
        local highest_container_num=${container_nums[0]}
        local last_container_name="${container_base_name}${highest_container_num}"
        echo "Scaling down: Removing container ${last_container_name}" | log_with_date
        sudo ansible-playbook /home/vmadm/demo/RapidServe/southbound/destroy_con.yaml --extra-vars "{\"container_name\": \"$container_name\", \"subnets\": \"${vpc_name}_S1\", \"vpc_name\": \"${vpc_name}\"}"
    fi
}

# Monitoring and scaling based on CPU usage
containers_above_threshold=0
running_containers=$(get_running_containers)
for ((i=1; i<=running_containers; i++)); do
    container_name="${container_base_name}${i}"
    if docker ps --format "{{.Names}}" | grep -q $container_name; then
        cpu_usage=$(check_cpu_usage "$container_name")
        if (( $(echo "$cpu_usage > $cpu_threshold" | bc -l) )); then
            ((containers_above_threshold++))
        fi
    fi
done

# Decide on scaling actions
if ((containers_above_threshold >= min_containers)); then
    scale_up
elif ((running_containers > min_containers && containers_above_threshold == 0)); then
    scale_down
else
    echo "No scaling required." | log_with_date
fi
