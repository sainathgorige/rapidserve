#!/bin/bash
sudo ip link delete NE_IN_S1_br type bridge
sudo ip link delete NE_IN_S2_br type bridge
sudo ip link delete NE_JA_S1_br type bridge
sudo ip link delete NE_JA_S2_br type bridge

# Deleting OVS bridges
# sudo ovs-vsctl del-br n1_sub2_br
# sudo ovs-vsctl del-br n1_sub1_br
# sudo ovs-vsctl del-br n2_sub2_br
# sudo ovs-vsctl del-br n2_sub1_br

# Deleting virtual ethernet (veth) pairs
sudo ip link delete NE_IN_S1_veth0
sudo ip link delete NE_IN_S2_veth0
sudo ip link delete NE_JA_S1_veth0
sudo ip link delete NE_JA_S2_veth0

# Deleting network namespaces
sudo ip netns delete NE_IN
sudo ip netns delete NE_JA

# Deleting additional veth interfaces
sudo ip link delete NE_IN_veth0
sudo ip link delete NE_JA_veth0

sudo ip link delete v_NE_JA_S1