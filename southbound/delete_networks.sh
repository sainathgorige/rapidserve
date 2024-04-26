#!/bin/bash

# Function to delete network elements for Netflix
delete_netflix() {
    # Deleting bridges
    sudo ip link delete NF_US_S1_br type bridge
    sudo ip link delete NF_US_S2_br type bridge
    sudo ip link delete NF_JP_S1_br type bridge
    sudo ip link delete NF_JP_S2_br type bridge

    # Deleting virtual ethernet (veth) pairs
    sudo ip link delete NF_US_S1_veth0
    sudo ip link delete NF_US_S2_veth0
    sudo ip link delete NF_JP_S1_veth0
    sudo ip link delete NF_JP_S2_veth0

    # Deleting network namespaces
    sudo ip netns delete NF_US
    sudo ip netns delete NF_JP

    # Deleting additional veth interfaces
    sudo ip link delete NF_US_veth0
    sudo ip link delete NF_JP_veth0
}

# Function to delete network elements for Hotstar
delete_hotstar() {
    # Deleting bridges
    sudo ip link delete HS_UK_S1_br type bridge
    sudo ip link delete HS_UK_S2_br type bridge
    sudo ip link delete HS_CN_S1_br type bridge
    sudo ip link delete HS_CN_S2_br type bridge

    # Deleting virtual ethernet (veth) pairs
    sudo ip link delete HS_UK_S1_veth0
    sudo ip link delete HS_UK_S2_veth0
    sudo ip link delete HS_CN_S1_veth0
    sudo ip link delete HS_CN_S2_veth0

    # Deleting network namespaces
    sudo ip netns delete HS_UK
    sudo ip netns delete HS_CN

    # Deleting additional veth interfaces
    sudo ip link delete HS_UK_veth0
    sudo ip link delete HS_CN_veth0
    echo "Deleting network elements for Hotstar"
}

# Function to delete network elements for Disney
delete_disney() {
     # Deleting bridges
    sudo ip link delete D_UK_S1_br type bridge
    sudo ip link delete D_UK_S2_br type bridge
    sudo ip link delete D_US_S1_br type bridge
    sudo ip link delete D_US_S2_br type bridge

    # Deleting virtual ethernet (veth) pairs
    sudo ip link delete D_UK_S1_veth0
    sudo ip link delete D_UK_S2_veth0
    sudo ip link delete D_US_S1_veth0
    sudo ip link delete D_US_S2_veth0

    # Deleting network namespaces
    sudo ip netns delete D_UK
    sudo ip netns delete D_US

    # Deleting additional veth interfaces
    sudo ip link delete D_UK_veth0
    sudo ip link delete D_US_veth0
    echo "Deleting network elements for Disney"
}

# Check the command-line argument to determine which function to run
if [ "$1" == "netflix" ]; then
    delete_netflix
elif [ "$1" == "hotstar" ]; then
    delete_hotstar
elif [ "$1" == "disney" ]; then
    delete_disney
else
    echo "Usage: $0 [netflix|hotstar|disney]"
    exit 1
fi
