#!/bin/bash

# List of interfaces to delete, adjust the patterns to match your interfaces
declare -a interfaces_to_delete=(rs_gr_sw_S1_v0 rs_ir_sw_S1_v0 rs_gr_sw_S2_v0 rs_ir_ch_S1_v0 dj_ge_veth0 dj_ge_S1_v0 rs_gr_dj_S1_v0 rs_ir_dj_S1_v0 dns_root dns_brins rs_he_gr_S1_v0 rs_ei_gr_S1_v0 rs_ei_ir_S1_v0 hi_ge_veth0 hi_ge_S1_v0 rs_ji_gr_S1_v0 rs_ji_ir_S1_v0 rs_mo_gr_S1_v0 rs_mo_ir_S1_v0 rs_jo_gr_S1_v0 ne_fr_S1_veth0 ho_ge_veth0 ho_fr_veth0 ta_ge_veth0 ta_ge_S1_veth0 rs_ch_gr_S1_v0 rs_ch_gr_S2_v0 rs_ch_ir_S1_v0)

for interface in "${interfaces_to_delete[@]}"; do
  if ip link show "$interface" &> /dev/null; then
    echo "Deleting interface: $interface"
    sudo ip link delete "$interface"
  else
    echo "Interface $interface not found, skipping..."
  fi
done

