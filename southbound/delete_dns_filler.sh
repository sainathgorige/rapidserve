#!/bin/bash

# Delete the network namespace
sudo ip netns delete dns_ns

# Delete the network interfaces
sudo ip link delete dns_br
sudo ip link delete dns_root
sudo ip link delete dns_brins
sudo ip link delete dns_nsbr
sudo ip link delete v_dns_veth
sudo ip link delete v_dns_r1 
sudo ip link delete dns_t2
sudo ip link delete dns_t1
sudo ip link delete v_dns_t1
sudo ip link delete v_dns_t2