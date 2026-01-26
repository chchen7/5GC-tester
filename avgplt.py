import csv
import matplotlib.pyplot as plt
import numpy as np
import os

base_filename = 'result-logs-{}-{}-{}-{}.csv'
cores = [0, 1]
cores_name = ['free5GC', 'Open5GS']
execs = list(range(1, 101))          
delays = [100, 200, 300, 400, 500]                     

experiments = [1, 3, 5, 7, 9, 11]     
MAX_UE_COUNT = 100 

colors = ['#f39c12', '#3498db'] 

fig, axes = plt.subplots(len(delays), 1, figsize=(12, 6 * len(delays)))
if len(delays) == 1: axes = [axes]

for d_idx, delay in enumerate(delays):
    ax = axes[d_idx]

    plot_data = {core: [] for core in cores}
    
    for core_idx, core in enumerate(cores):
        for exp in experiments:
            all_completion_times = []
            
            for exe in execs:
                file_path = base_filename.format(exe, core, delay, exp)
                
                if os.path.exists(file_path):
                    try:
                        with open(file_path, newline='') as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                dp_raw = row.get('DataPlaneReady', "").strip()
                                if dp_raw: 
                                    all_completion_times.append(float(dp_raw))
                    except Exception:
                        pass

            plot_data[core].append(all_completion_times)

    width = 0.3 
    x_indices = np.arange(len(experiments))
    
    for core_idx, core in enumerate(cores):
        pos = x_indices + (core_idx - 0.5) * width * 1.2

        bplot = ax.boxplot(
            plot_data[core],
            positions=pos,
            widths=width,
            patch_artist=True,
            flierprops={'markeredgecolor': colors[core_idx], 'markersize': 2, 'alpha': 0.5},

            medianprops={'color': colors[core_idx], 'linewidth': 2},

            boxprops={'facecolor': 'none', 'color': colors[core_idx], 'linewidth': 1.5},
            whiskerprops={'color': colors[core_idx]},
            capprops={'color': colors[core_idx]}
        )

    ax.set_title(f"Injection Delay: {delay} ms (Completion Time Distribution)", loc='right', fontweight='bold')
    ax.set_ylabel("DataPlaneReady (Time)")
    ax.set_xlabel("Number of gNBs")
    
    ax.set_xticks(x_indices)
    ax.set_xticklabels(experiments)

    ax.grid(axis='y', linestyle='--', alpha=0.3)

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color=colors[0], lw=2, label='free5GC'),
        Line2D([0], [0], color=colors[1], lw=2, label='Open5GS')
    ]
    ax.legend(handles=legend_elements, loc='upper left', frameon=True)

plt.tight_layout()
plt.savefig('completion_time_boxplot.png', dpi=300)
plt.show()