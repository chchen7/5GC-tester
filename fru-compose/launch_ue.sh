#!/bin/bash

UE_COUNT=1
INTERVAL=1000
IMSI=208930000000001
GNB_ID=1

while getopts "n:t:i:g:" opt; do
  case $opt in
    n) UE_COUNT=$OPTARG ;;
    t) INTERVAL=$OPTARG ;;
    i) IMSI=$OPTARG ;;
    g) GNB_ID=$OPTARG ;;
    *) echo "Usage: $0 -n [COUNT] -t [INTERVAL_MS] -i [START_IMSI] -g [GNB_ID]" >&2; exit 1 ;;
  esac
done

if ! [[ "$UE_COUNT" =~ ^[0-9]+$ ]]; then
    echo "[ERROR] UE count must be a number: $UE_COUNT" >&2
    exit 1
fi

TARGET_GNB="fru-compose-gnb-$GNB_ID"
NEW_MSIN=${IMSI:5}

CONFIG_FILE="uecfg.yaml"
OUTPUT_FILE="uecfg_scaled.yaml"

sed -e "s/msin: \".*\"/msin: \"$NEW_MSIN\"/" \
    -e "s/ranControlPlaneIp: .*/ranControlPlaneIp: $TARGET_GNB/" \
    -e "s/ranDataPlaneIp: .*/ranDataPlaneIp: $TARGET_GNB/" \
    $CONFIG_FILE > $OUTPUT_FILE

LOG_FILE="ue.log"
./free-ran-ue ue -c $OUTPUT_FILE -n $UE_COUNT -t $INTERVAL > "$LOG_FILE" 2>&1 &