#!/bin/bash

UE_COUNT=1
INTERVAL=1000
IMSI=208930000000001
while getopts "n:t:i:" opt; do
  case $opt in
    n) UE_COUNT=$OPTARG ;;
    t) INTERVAL=$OPTARG ;;
    i) IMSI=$OPTARG ;;
    *) echo "Usage: $0 -n [COUNT] -t [INTERVAL_MS] -i [START_IMSI]" >&2; exit 1 ;;
  esac
done

if ! [[ "$UE_COUNT" =~ ^[0-9]+$ ]]; then
    echo "[ERROR] UE count must be a number: $UE_COUNT" >&2
    exit 1
fi

if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]]; then
    echo "[ERROR] Interval must be a number: $INTERVAL" >&2
    exit 1
fi
LOG_DIR="/ueransim/logs"
mkdir -p "$LOG_DIR"

for i in $(seq 1 $UE_COUNT); do
    LOG_FILE="$LOG_DIR/ue-$i.log"
    CURRENT_IMSI=$((IMSI + i - 1))
    ./nr-ue -c /ueransim/config/uecfg.yaml -i imsi-$CURRENT_IMSI > "$LOG_FILE" 2>&1 &
    SLEEP_SEC=$(printf "%d.%03d" $((INTERVAL / 1000)) $((INTERVAL % 1000)))
    if [ "$i" -lt "$UE_COUNT" ]; then
        sleep "$SLEEP_SEC"
    fi
done

echo "[SUCCESS] All launch commands initiated."