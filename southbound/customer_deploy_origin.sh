#!/bin/bash

#set -x
# Check if correct number of arguments was provided

usage() {
    echo "Usage: $0 <tenant_name> <region_prefix>"
    echo "Arguments:"
    echo "  tenant_name    The name of the tenant"
    echo "  region_prefix  The region where the tenant is located"
    exit 1
}

# Check if the first argument is --help
if [ "$1" = "--help" ]; then
    usage
fi
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <tenant_name> <region>"
    exit 1
fi

# Capture inputs
tenant_name=$1
region=$2

# Extract the first two letters of the tenant name
tenant_prefix=${tenant_name:0:2}

# Lowercase conversion if needed (optional, based on your naming conventions)
tenant_prefix=$(echo "$tenant_prefix" | tr '[:upper:]' '[:lower:]')

# Form the container name
container_name="${tenant_prefix}_${region}_container1"

echo "Container Name: $container_name"

# Define paths to your configuration and template files
index_template="/home/vmadm/demo/RapidServe/southbound/index.html.j2"
nginx_origin_conf="/home/vmadm/demo/RapidServe/southbound/nginx-origin.conf"
nginx_edge_template="/home/vmadm/demo/RapidServe/southbound/nginx-edge.conf.j2"
temp_nginx_conf=$(mktemp)  # Temporary file to store the modified nginx configuration

# Check if necessary files exist
if [[ ! -f "$index_template" || ! -f "$nginx_origin_conf" || ! -f "$nginx_edge_template" ]]; then
    echo "One or more configuration files are missing."
    exit 1
fi

short_name="${container_name:0:8}${container_name: -2}"

# Update the HTML file and prepare it for mounting
sed "s/{{ tenant_name }}/$tenant_name/" "$index_template" > "/tmp/$tenant_prefix-index.html"

docker stop "$container_name" && docker rm -f "$container_name"

# Optional: sleep for a couple of seconds if you encounter issues with immediate re-run
# sleep 2

# Attempt to run a new container using the same name
if ! docker run --cap-add=NET_ADMIN --name "$container_name" --network none -d -v "/tmp/$tenant_prefix-index.html:/var/www/html/index.html" 100514735019/customer_image; then
    echo "Failed to start the container. Retrying..."
    # Optional: Retry mechanism if the first attempt fails
    sleep 2
    docker run --cap-add=NET_ADMIN --name "$container_name" --network none -d -v "/tmp/$tenant_prefix-index.html:/var/www/html/index.html" 100514735019/customer_image || {
        echo "Failed to start container on second attempt."
        exit 1
    }
fi

# Copy the nginx config into the container
docker cp "$nginx_origin_conf" "$container_name:/etc/nginx/nginx.conf"

# Attempt to reload nginx, handle failure
if ! docker exec "$container_name" nginx -s reload; then
    echo "Failed to reload Nginx on $container_name."
    #exit 1
fi
sudo rm -f "/var/run/netns/$container_name"
docker_pid=$(docker inspect --format '{{.State.Pid}}' "$container_name")
sudo ln -sf "/proc/$docker_pid/ns/net" "/var/run/netns/$container_name"
sudo ip link add  ${short_name} type veth peer name "v_${short_name}"
sudo ip link set "v_${short_name}" up
subnet_prefix="${container_name%_container*}"
sudo ip link set "v_${short_name}" master "${subnet_prefix}_S1_br"
sudo ip link set "$short_name" netns "$container_name"
sudo ip netns exec ${container_name} ip link set ${short_name} up
docker exec ${container_name} dhclient ${short_name}

origin_ip=$(docker exec "$container_name" sh -c "ip addr show dev ${short_name} | grep 'inet ' | awk '{print \$2}' | cut -d'/' -f1")

echo $origin_ip
# Process and deploy nginx configuration for edge servers
sed "s/{{ vm_ip }}/$origin_ip/" "$nginx_edge_template" > "$temp_nginx_conf"

# Get all other containers that start with the tenant name prefix but aren't the specified container
container_prefix="${container_name::-1}"
containers=$(docker ps --filter "name=^${container_prefix}" --format "{{.Names}}" | grep -v "^$container_name$")

# Update nginx configuration for all edge containers and reload nginx
for cont in $containers; do
    docker cp "$temp_nginx_conf" "$cont:/etc/nginx/nginx.conf"
    docker exec "$cont" nginx -s reload
done

# Clean up temporary files
rm "$temp_nginx_conf"

echo "Nginx configurations updated and servers reloaded."
