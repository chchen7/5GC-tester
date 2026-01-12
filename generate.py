import subprocess
import pandas as pd
import re
from datetime import datetime
import sys
import argparse
import tarfile
import io
import os

DEFAULT_GNB_START = 1
DEFAULT_GNB_COUNT = 1
DEFAULT_UE_COUNT = 100
OUTPUT_FILENAME = "ueransim_metrics.csv"

CONTAINER_LOG_PATH = "/ueransim/logs"

DOCKER_CMD_TEMPLATE = f"docker cp ueransim-ueransim-gnb-{{gnb_id}}:{CONTAINER_LOG_PATH} -"


TIME_PATTERN = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]')
REG_REQ_PATTERN = re.compile(r"Sending Initial Registration")
FILENAME_UE_ID_PATTERN = re.compile(r"ue-(\d+)\.log")

EVENT_PATTERNS = {
    "MM5G_DEREGISTERED": re.compile(r"UE switches to state \[MM-DEREGISTERED/PLMN-SEARCH\]"),
    "MM5G_REGISTER_REQ": re.compile(r"Sending Initial Registration"),
    "MM5G_REGISTERED_INITIATED": re.compile(r"UE switches to state \[MM-REGISTER-INITIATED\]"),
    "MM5G_REGISTERED": re.compile(r"UE switches to state \[MM-REGISTERED/NORMAL-SERVICE\]"),
    "SM5G_PDU_SESSION_ACTIVE_PENDING": re.compile(r"Sending PDU Session Establishment Request"),
    "SM5G_PDU_SESSION_ACTIVE": re.compile(r"PDU Session establishment is successful"),
    "DataPlaneReady": re.compile(r"TUN interface.*is up")
}

def get_all_logs_from_gnb(gnb_id):
   
    cmd = DOCKER_CMD_TEMPLATE.format(gnb_id=gnb_id)
    try:

        result = subprocess.run(cmd, shell=True, capture_output=True)
        
        if result.returncode != 0:

            err_msg = result.stderr.decode('utf-8', errors='ignore').strip()
            print(f"[Error] Failed to cp logs from gNB-{gnb_id}.", file=sys.stderr)
            print(f"       Message: {err_msg}", file=sys.stderr)
            print(f"       Check if path '{CONTAINER_LOG_PATH}' exists in the container.", file=sys.stderr)
            return {}
        
        logs_dict = {}

        with tarfile.open(fileobj=io.BytesIO(result.stdout), mode='r|') as tar:
            for member in tar:
                if member.isfile():

                    fname = os.path.basename(member.name)
                    match = FILENAME_UE_ID_PATTERN.search(fname)
                    if match:
                        ue_id = int(match.group(1))
                        f = tar.extractfile(member)
                        if f:
                            content = f.read().decode('utf-8', errors='ignore')
                            logs_dict[ue_id] = content
        return logs_dict
    except Exception as e:
        print(f"[Exception] {e}", file=sys.stderr)
        return {}

def parse_log(log_text, current_gnb_id, current_ue_id):
    data = {
        "gnbid": f"{current_gnb_id}",
        "ueid": current_ue_id,
        "type": 3,
        "timestamp": None,
        "SM5G_PDU_SESSION_INACTIVE": 0.0,
        "MM5G_NULL": 0.0,
        "MM5G_DEREGISTERED": None,
        "MM5G_REGISTER_REQ": None,
        "MM5G_REGISTERED_INITIATED": None,
        "MM5G_REGISTERED": None,
        "SM5G_PDU_SESSION_ACTIVE_PENDING": None,
        "SM5G_PDU_SESSION_ACTIVE": None,
        "DataPlaneReady": None
    }

    if not log_text:
        return data

    lines = log_text.strip().split('\n')
    start_time = None

    for line in lines:
        if REG_REQ_PATTERN.search(line):
            time_match = TIME_PATTERN.search(line)
            if time_match:
                start_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S.%f')
                data["timestamp"] = int(start_time.timestamp() * 1e9)
                data["MM5G_REGISTER_REQ"] = 0.0
                break

    if start_time is not None:
        for line in lines:
            time_match = TIME_PATTERN.search(line)
            if not time_match:
                continue
            
            current_dt = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S.%f')
            delta_ms = (current_dt - start_time).total_seconds() * 1000

            for column, pattern in EVENT_PATTERNS.items():
                if column == "MM5G_REGISTER_REQ":
                    continue
                
                if data[column] is None and pattern.search(line):
                    data[column] = round(delta_ms, 6)

    return data

def parse_arguments():
    parser = argparse.ArgumentParser(description="Fast Parse UERANSIM Docker logs (Rescue Mode).")
    parser.add_argument("--gnb-start", type=int, default=DEFAULT_GNB_START, help="Starting gNB ID")
    parser.add_argument("--gnb-count", type=int, default=DEFAULT_GNB_COUNT, help="Total number of gNBs")
    parser.add_argument("--ue-count", type=int, default=DEFAULT_UE_COUNT, help="Number of UEs per gNB")
    parser.add_argument("-o", "--output", type=str, default=OUTPUT_FILENAME, help="Output CSV filename")
    return parser.parse_args()

def main():
    args = parse_arguments()
    target_ids = range(args.gnb_start, args.gnb_start + args.gnb_count)
    target_ue_set = set(range(1, args.ue_count + 1))
    
    output_file = args.output
    all_rows = []
    
    print(f"Starting RESCUE processing (using docker cp)...")
    print(f"Target Log Path: {CONTAINER_LOG_PATH}")
    print(f"Target gNB IDs : {list(target_ids)}")
    print("-" * 40)
    
    for gnb_id in target_ids:
        print(f"Extracting logs from gNB-{gnb_id}...")
        logs_map = get_all_logs_from_gnb(gnb_id)
        
        if not logs_map:
            print(f"  -> No logs retrieved.")
            continue
            
        print(f"  -> Retrieved {len(logs_map)} log files. Parsing...")

        for ue_id in sorted(list(logs_map.keys())):
            if ue_id in target_ue_set:
                log_content = logs_map[ue_id]
                row = parse_log(log_content, gnb_id, ue_id)
                all_rows.append(row)
            
    print(f"\nProcessing complete. Total rows: {len(all_rows)}")

    if all_rows:
        df = pd.DataFrame(all_rows)
        cols_order = [
            "gnbid", "ueid", "type", "timestamp", 
            "SM5G_PDU_SESSION_INACTIVE", "MM5G_NULL",
            "MM5G_DEREGISTERED", "MM5G_REGISTER_REQ",
            "MM5G_REGISTERED_INITIATED", "MM5G_REGISTERED",
            "SM5G_PDU_SESSION_ACTIVE_PENDING", "SM5G_PDU_SESSION_ACTIVE", "DataPlaneReady"
        ]
        for col in cols_order:
            if col not in df.columns:
                df[col] = None
        df = df[cols_order]
        df = df.sort_values(by=["gnbid", "ueid"])
        df.to_csv(output_file, index=False, na_rep='')
        print(f"Successfully saved to {output_file}")
    else:
        print("No valid data collected.")

if __name__ == "__main__":
    main()