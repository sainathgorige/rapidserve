#!/bin/bash

# Function to get IP address of all VMs in a region and tenant
get_region_tenant_vm_ips() {
    region_tenant=$1
    username="root"
    password="admin"

    # Determine the regular expression to use based on the input
    if [[ "$region_tenant" =~ ^[A-Z]{2}_[A-Z]+ ]]; then
        regex="${region_tenant//_/[_A-Z]*}_VM[0-9]+"
    elif [[ "$region_tenant" =~ ^[A-Z]{2}$ ]]; then
        regex="${region_tenant}_.*_VM[0-9]+"
    else
        echo "Invalid input. Please provide a valid region and tenant combination."
        exit 1
    fi

    # Use virsh list to get all VMs and filter based on the provided region and tenant
    vms=($(virsh list --all | grep -E "$regex" | awk '{print $2}'))

    # Use expect to automate interaction with virsh console for each VM
    ips=()
    for vm_name in "${vms[@]}"; do
        ip=$(expect -c "
            spawn virsh console $vm_name
            expect \"Escape character\"
            send \"\r\"
            expect \"login:\"
            send \"$username\r\"
            expect \"Password:\"
            send \"$password\r\"
            expect \"\#\"
            send \"ip -o -4 addr show ens2 | awk '{print \\\$4}' | cut -d/ -f1\r\"
            expect {
                \"No such device\" {
                    send \"ip -o -4 addr show ens3 | awk '{print \\\$4}' | cut -d/ -f1\r\"
                }
            }
            expect \"\#\"
            send \"exit\r\"
            expect eof
        " | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b")

        ips+=("$ip")
    done

    # Output IP addresses separated by newline
    printf "%s\n" "${ips[@]}"
}

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <region_tenant>"
    exit 1
fi

# Replace "NF_JP" with the region you want to get VM IPs for
get_region_tenant_vm_ips "$1"
