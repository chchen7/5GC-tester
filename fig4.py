import csv
import matplotlib.pyplot as plt
import numpy as np
import os

base_filename = './{}c{}g/result-iperf-{}-{}-{}-{}.csv'

configs = [(12, 8), (8, 8), (6, 8), (4, 4)]
core_info = [
    {'name': 'free5gc', 'id': 0, 'display': 'free5GC'},
    {'name': 'open5gs', 'id': 1, 'display': 'Open5GS'}
]
ue_counts = [1, 4, 8]
experiments = range(1,11)

csv_headers = ['timestamp', 'source_addr', 'source_port', 'dest_addr', 'dest_port', 'id', 'interval', 'bytes', 'bps']

plt.style.use('seaborn-v0_8-whitegrid')
fig, axes = plt.subplots(len(configs), len(core_info), figsize=(12, 14), sharey=True)

for row_idx, (cpu, ram) in enumerate(configs):
    config_str = f"{cpu}c{ram}g"
    for col_idx, core in enumerate(core_info):
        ax = axes[row_idx, col_idx]

        for exp_ue_count in ue_counts:
            stacked_ue_averages = []

            for ue_id in range(exp_ue_count):
                temp_exes = []
                for exe in experiments:
                    file_path = base_filename.format(
                        cpu, ram, exe, core['id'], exp_ue_count, ue_id+1
                    )
                    
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f, fieldnames=csv_headers)
                            rows = list(reader)
                            val = 0
                            for r in rows:
                                if r['interval'] == '0.0-60.0':
                                    val = float(r['bps']) / 1e6
                                    break
                            if val > 0:
                                temp_exes.append(val)

                if temp_exes:
                    stacked_ue_averages.append(np.mean(temp_exes))

            bottom = 0
            colors = plt.cm.tab10(np.linspace(0, 1, 10))
            for i, val in enumerate(stacked_ue_averages):
                ax.bar(str(exp_ue_count), val, bottom=bottom, width=0.6,
                       color=colors[i % 10], edgecolor='white', linewidth=0.8)
                bottom += val

        if row_idx == 0:
            ax.set_title(core['display'], fontsize=15, fontweight='bold', pad=12)
        else:
            ax.set_title("")

        if col_idx == 0:
            ax.set_ylabel(config_str, fontsize=11, fontweight='bold', rotation=0, labelpad=40, va='center')

        ax.tick_params(labelbottom=True, labelleft=True, labelsize=9)
        ax.set_ylim(0, 1400) 

fig.text(0.04, 0.5, 'Throughput (Mbps)', va='center', rotation='vertical', fontsize=13, fontweight='bold')
fig.text(0.5, 0.04, 'Number of UEs', ha='center', fontsize=13, fontweight='bold')

plt.subplots_adjust(left=0.15, bottom=0.08, right=0.95, top=0.94, hspace=0.2, wspace=0.1)

plt.savefig('fig_4.png', dpi=300, bbox_inches='tight')