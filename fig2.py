import csv
import matplotlib.pyplot as plt
import numpy as np
import os

def sliding_window_mean(arr, window=5):
    arr = np.array(arr, dtype=float)
    if len(arr) < window:
        return arr
    try:
        windows = np.lib.stride_tricks.sliding_window_view(arr, window)
        with np.errstate(divide='ignore', invalid='ignore'):
            smooth = np.nanmean(windows, axis=1)
        return smooth
    except Exception:
        return arr

base_filename = 'result-logs-{}-{}-{}-{}.csv'
cores = [0, 1]
cores_name = ['free5GC', 'Open5GS']
execs = list(range(1, 11))             
delays = [500, 400, 300, 200, 100]     
experiments = [1, 3, 5, 7, 9, 11]     
MAX_UE_COUNT = 100                     

MAX_AXIS_ROW = 5  
MAX_AXIS_COL = 2  

plt.rcParams["figure.figsize"] = (14, 20)
plt.rcParams['figure.subplot.hspace'] = 0.5
plt.rcParams['figure.subplot.wspace'] = 0.3
figure, axis = plt.subplots(MAX_AXIS_ROW, MAX_AXIS_COL)

for core_idx, core in enumerate(cores):
    for delay_idx, delay in enumerate(delays):
        
        ax = axis[delay_idx, core_idx]

        expected_total_time = (MAX_UE_COUNT - 1) * (delay / 1000.0)
        
        for exp in experiments:
            all_dataplaneready = []
            
            for exe in execs:

                one_exec_data = np.full(MAX_UE_COUNT, np.nan)
                
                file_path = base_filename.format(exe, core, delay, exp)
                
                if os.path.exists(file_path):
                    try:
                        with open(file_path, newline='') as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                ueid_str = row.get('ueid')
                                if not ueid_str: continue
                                
                                ue_idx = int(ueid_str) - 1 
                                if ue_idx >= MAX_UE_COUNT: continue

                                dp_raw = row.get('DataPlaneReady', "").strip()
                                if dp_raw != "" and dp_raw is not None:
                                    try:
                                        one_exec_data[ue_idx] = float(dp_raw)
                                    except ValueError:
                                        pass
                    except Exception:
                        pass
                
                all_dataplaneready.append(one_exec_data)

            with np.errstate(divide='ignore', invalid='ignore'):
                avg_dp = np.nanmean(all_dataplaneready, axis=0)

            theoretical_ts = np.arange(MAX_UE_COUNT) * (delay / 1000.0)
            

            smooth_dp = sliding_window_mean(avg_dp, window=5)

            smooth_ts = theoretical_ts[len(theoretical_ts) - len(smooth_dp):]
            
            ax.scatter(
                smooth_ts,
                smooth_dp,
                label="#gNB {}".format(exp),
                s=6,
                alpha=0.8
            )

        ax.set_title("{} (Delay {}ms)".format(cores_name[core_idx], delay), fontsize=12, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.5)

        ax.set_xlim(-1, expected_total_time + 2) 
        
        if delay_idx == MAX_AXIS_ROW - 1: 
            ax.set_xlabel("Injection Timeline (seconds)")
        if core_idx == 0: 
            ax.set_ylabel("DataPlaneReady (ns)")
        
        ax.legend(fontsize=7, markerscale=1.2, loc='upper right')

plt.tight_layout()
plt.savefig('fig2.png', dpi=300, bbox_inches='tight')
plt.close(figure)