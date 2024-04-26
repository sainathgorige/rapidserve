#!/bin/bash

# Destroy the VM named dns_server_vm
echo "Destroying the VM: dns_server_vm"
virsh destroy dns_server_vm

# Undefine the VM named dns_server_vm
echo "Undefining the VM: dns_server_vm"
virsh undefine dns_server_vm

# Delete the network namespace named dns_vpc
echo "Deleting the network namespace: dns_vpc"
sudo ip netns delete dns_vpc

# Delete the network link named dns_bridge
echo "Deleting the network link: dns_bridge"
sudo ip link delete dns_bridge

# Delete the network link named dns_root
echo "Deleting the network link: dns_root"
sudo ip link delete dns_root

# Delete the network link named dns_bridgens
echo "Deleting the network link: dns_bridgens"
sudo ip link delete dns_bridgens

sudo rm -rf /var/lib/libvirt/images/dns_server_vm

echo "Operations completed."
