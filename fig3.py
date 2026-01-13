import csv
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import os

base_filename = 'result-logs-{}-{}-{}-{}.csv' 
cores = [0, 1] 
cores_name = ['free5GC', 'Open5GS'] 

execs = list(range(1, 11))
delays = [500, 400, 300, 200, 100]
experiments = [1, 3, 5, 7, 9, 11]

data_results = {
    0: {d: [[] for _ in experiments] for d in delays}, # free5GC
    1: {d: [[] for _ in experiments] for d in delays}  # Open5GS
}

for core in cores:
    for delay in delays:
        for exp_idx, exp in enumerate(experiments):
            
            for exe in execs:
                file_path = base_filename.format(exe, core, delay, exp)
                
                if os.path.exists(file_path):
                    total_detected_ue = 0
                    success_count = 0
                    
                    try:
                        with open(file_path, newline='') as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                if row.get('ueid'):
                                    total_detected_ue += 1
                                    
                                    dp_raw = row.get('DataPlaneReady', "").strip()
                                    if dp_raw and dp_raw.lower() != "nan":
                                        success_count += 1
                                        
                        if total_detected_ue > 0:
                            fail_rate = ((total_detected_ue - success_count) / total_detected_ue) * 100
                            data_results[core][delay][exp_idx].append(fail_rate)
                            
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")

fig, axes = plt.subplots(nrows=len(delays), ncols=1, figsize=(10, 16), sharex=True)

colors = {0: "#f5a623", 1: "#4a90e2"}

for ax, delay in zip(axes, delays):
    for c in cores:
        pos_offset = -0.2 if c == 0 else 0.2
        
        plot_data = data_results[c][delay]
        
        ax.boxplot(
            plot_data,
            positions=np.arange(len(experiments)) + pos_offset,
            widths=0.3,
            patch_artist=True,
            boxprops=dict(facecolor='none', edgecolor=colors[c]),
            medianprops=dict(color=colors[c], linewidth=2),
            capprops=dict(color=colors[c]),
            whiskerprops=dict(color=colors[c]),
            showfliers=True,
            flierprops=dict(marker='o', markersize=3, markeredgecolor=colors[c])
        )

    ax.set_ylabel("Fail rate (%)")
    ax.set_title(f"Injection Delay: {delay} ms", fontsize=11, fontweight='bold', loc='right')
    ax.set_ylim(-5, 105)
    ax.grid(axis='y', linestyle=':', alpha=0.6)

axes[-1].set_xticks(np.arange(len(experiments)))
axes[-1].set_xticklabels(experiments)
axes[-1].set_xlabel("Number of gNBs")

legend_patches = [
    Patch(facecolor='none', edgecolor=colors[0], label='free5GC'),
    Patch(facecolor='none', edgecolor=colors[1], label='Open5GS')
]
fig.legend(handles=legend_patches, loc="upper center", ncol=2, frameon=False, fontsize=12)

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig("fig3.png", dpi=300)