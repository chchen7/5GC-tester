import subprocess
import pandas as pd
import re
from datetime import datetime
import sys
import argparse
import os

# --- Configuration ---
DEFAULT_GNB_START = 1
DEFAULT_GNB_COUNT = 1
DEFAULT_UE_COUNT = 100
OUTPUT_METRICS = "ue_metrics.csv"
REMOTE_LOG_PATH = "/free-ran-ue/ue.log" 
TEMP_LOCAL_FILE = "temp_ue_download.log"

# --- Core Regex ---
# Matches Date, Time, 10-digit UE ID, and Message
LOG_REGEX = re.compile(r'(\d{4}/\d{2}/\d{2}).*?(\d{2}:\d{2}:\d{2}\.\d+).*?(\d{10}).*?\]\s+(.*)')
# ANSI Escape Sequence Filter (Removes color codes that block regex matching)
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# 5G Key Event Patterns
EVENT_PATTERNS = {
    "MM5G_REGISTER_REQ": re.compile(r"Processing UE Registration"),
    "MM5G_REGISTERED": re.compile(r"UE Registration finished"),
    "SM5G_PDU_SESSION_ACTIVE_PENDING": re.compile(r"Processing PDU session establishment"),
    "SM5G_PDU_SESSION_ACTIVE": re.compile(r"PDU session establishment complete"),
    "DataPlaneReady": re.compile(r"UE tunnel device setup as")
}

def get_log_via_cp(gnb_id):
    container_name = f"fru-compose-ue-{gnb_id}"
    print(f"[*] Extracting logs from container: {container_name}")
    cmd = f"docker cp {container_name}:{REMOTE_LOG_PATH} ./{TEMP_LOCAL_FILE}"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [!] CP Failed for {container_name}. Skip.")
        return None
        
    if os.path.exists(TEMP_LOCAL_FILE):
        with open(TEMP_LOCAL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        os.remove(TEMP_LOCAL_FILE)
        return content
    return None

def process_content(log_text, gnb_id):
    ue_results = {}
    lines = log_text.strip().split('\n')
    
    total_log_lines = len(lines)
    id_matched_count = 0
    
    for line in lines:
        clean_line = ANSI_ESCAPE.sub('', line).strip()
        match = LOG_REGEX.search(clean_line)
        
        if not match:
            continue
            
        id_matched_count += 1
        date_part, time_part, ue_id_str, msg = match.groups()
        ue_id = int(ue_id_str)
        ts_str = f"{date_part} {time_part}"
        dt = datetime.strptime(ts_str, '%Y/%m/%d %H:%M:%S.%f')
        
        if ue_id not in ue_results:
            ue_results[ue_id] = {
                "gnbid": f"{gnb_id}", "ueid": ue_id, "type": 3,
                "timestamp": int(dt.timestamp() * 1e9), "start_dt": dt,
                "MM5G_REGISTER_REQ": None, "MM5G_REGISTERED": None,
                "SM5G_PDU_SESSION_ACTIVE_PENDING": None, "SM5G_PDU_SESSION_ACTIVE": None,
                "DataPlaneReady": None
            }
        
        res = ue_results[ue_id]
        
        if EVENT_PATTERNS["MM5G_REGISTER_REQ"].search(msg):
            res["start_dt"] = dt
            res["timestamp"] = int(dt.timestamp() * 1e9)
            res["MM5G_REGISTER_REQ"] = 0.0
        
        if res["start_dt"] is not None:
            delta_ms = (dt - res["start_dt"]).total_seconds() * 1000
            for col, pattern in EVENT_PATTERNS.items():
                if col == "MM5G_REGISTER_REQ": continue
                if res[col] is None and pattern.search(msg):
                    res[col] = round(delta_ms, 6)

    return list(ue_results.values()), total_log_lines, id_matched_count

def main():
    parser = argparse.ArgumentParser(description="Multi-gNB Log Metric Parser")
    parser.add_argument("--gnb-start", type=int, default=DEFAULT_GNB_START, help="Starting gNB/Container ID")
    parser.add_argument("--gnb-count", type=int, default=DEFAULT_GNB_COUNT, help="Number of gNBs to process")
    parser.add_argument("--ue-count", type=int, default=DEFAULT_UE_COUNT, help="UEs per gNB to parse")
    parser.add_argument("-o", "--output", default=OUTPUT_METRICS)
    args = parser.parse_args()

    all_metrics = []

    # Loop through the specified range of gNB IDs
    target_gnb_range = range(args.gnb_start, args.gnb_start + args.gnb_count)
    
    for g_id in target_gnb_range:
        content = get_log_via_cp(g_id)
        if content:
            metrics, total, matched = process_content(content, g_id)
            # Filter by UE count if needed
            filtered = [m for m in metrics if m['ueid'] <= args.ue_count]
            all_metrics.extend(filtered)
            
            print("-" * 45)
            print(f" gNB-{g_id} Summary:")
            print(f"  - Total Lines: {total} | Matched: {matched}")
            print(f"  - UEs Found:   {len(metrics)}")

    if all_metrics:
        df_m = pd.DataFrame(all_metrics)
        if 'start_dt' in df_m.columns:
            df_m = df_m.drop(columns=['start_dt'])
        
        cols = ["gnbid", "ueid", "type", "timestamp", "MM5G_REGISTER_REQ", "MM5G_REGISTERED", 
                "SM5G_PDU_SESSION_ACTIVE_PENDING", "SM5G_PDU_SESSION_ACTIVE", "DataPlaneReady"]
        for c in cols:
            if c not in df_m.columns: df_m[c] = None
        
        df_m[cols].sort_values(by=["gnbid", "ueid"]).to_csv(args.output, index=False, na_rep='')
        
        print("=" * 45)
        print(" Global Event Parsing Summary (Total Count):")
        for col in cols[4:]:
            print(f"  {col:32}: {df_m[col].notnull().sum()}")
        print("=" * 45)
        print(f"[Success] Data exported to: {args.output}")
    else:
        print("\n[Error] No valid data found in the specified gNB range.")

if __name__ == "__main__":
    main()