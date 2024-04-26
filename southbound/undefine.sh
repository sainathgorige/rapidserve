#!/bin/bash

# Get the list of VMs and store it in a variable
vms=$(virsh list --all | grep shut | awk '{print $2}')

# Loop through each shut-off VM and undefine it
for vm in $vms; do
    virsh undefine $vm
done
