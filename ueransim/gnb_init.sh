#!/bin/bash
NODE_ID=$(ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 | cut -d. -f4)

GNB_NCI=$(printf ''0x%09x'' $NODE_ID)
sed "s/{GNB_NCI}/'$GNB_NCI'/g" ./config/gnbcfg.yaml > ./config/gnbcfg-scaled.yaml
./nr-gnb -c /ueransim/config/gnbcfg-scaled.yaml
