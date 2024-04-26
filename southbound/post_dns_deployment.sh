#!/bin/bash

# Check if a tenant name was provided
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <tenant_name>"
  exit 1
fi

# Assign the first script argument to TENANT_NAME
TENANT_NAME="$1"

# Step 1: Run DNS Setup with specified inventory
echo "Starting DNS setup for tenant $TENANT_NAME..."
ansible-playbook -i inventory_dns.ini implement_dns.yaml -e "tenant_name=$TENANT_NAME"

# Check if the DNS setup was successful
if [ $? -ne 0 ]; then
  echo "DNS setup failed for tenant $TENANT_NAME. Exiting..."
  exit 1
fi

echo "DNS setup completed successfully for tenant $TENANT_NAME."

# Step 2: Run Load Balancing Setup targeting localhost
echo "Starting Load Balancing setup for tenant $TENANT_NAME..."
sudo ansible-playbook implement_loadbalancing.yaml -e "tenant_name=$TENANT_NAME"

# Check if the Load Balancing setup was successful
if [ $? -ne 0 ]; then
  echo "Load Balancing setup failed for tenant $TENANT_NAME. Exiting..."
  exit 1
fi

echo "Load Balancing setup completed successfully for tenant $TENANT_NAME."
