#!/bin/bash

IP_CORE=$(hostname -I | tr ' ' '\n' | grep -E '172.22\.|10.100.200\.' | head -n 1)

IP_RAN=$(hostname -I | tr ' ' '\n' | grep '10.0.2.')

NODE_ID=$(echo $IP_RAN | cut -d. -f4)
GNB_ID=$(printf "%06x" $NODE_ID)
GNB_NAME="gNB-$NODE_ID"

CONFIG_FILE="gnbcfg.yaml"
OUTPUT_FILE="gnbcfg-scaled.yaml"

sed -e "s/ranN2Ip: .*/ranN2Ip: \"$IP_CORE\"/" \
    -e "s/ranN3Ip: .*/ranN3Ip: \"$IP_CORE\"/" \
    -e "s/ranControlPlaneIp: .*/ranControlPlaneIp: \"$IP_RAN\"/" \
    -e "s/ranDataPlaneIp: .*/ranDataPlaneIp: \"$IP_RAN\"/" \
    -e "s/ip: .*/ip: \"$IP_CORE\"/" \
    -e "s/gnbId: \".*\"/gnbId: \"$GNB_ID\"/" \
    --e "s/gnbName: \".*\"/gnbName: \"$GNB_NAME\"/" \
    $CONFIG_FILE > $OUTPUT_FILE

echo "[*] FINISH！"
echo ">>> CORE RAN IP (N2/N3): $IP_CORE"
echo ">>> UE RAN IP (RAN): $IP_RAN"
echo ">>> gNB ID: $GNB_ID"


./free-ran-ue gnb -c $OUTPUT_FILE