import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

base_filename = 'result-logs-influxdb-{}-{}-{}-{}.csv'

exes = range(1, 11)                
cores = [0, 1]                     
delays = [500, 400, 300, 200, 100] 
experiments = [1, 3, 5, 7, 9, 11]  
num_cores = 8                    
TIME_LIMIT = 80                    

core_info = [
    {'id': 0, 'label': 'free5GC'},
    {'id': 1, 'label': 'Open5GS'}
]

CORE_NF_NAMES = [
    '/amf', '/ausf', '/nrf', '/nssf', '/pcf', '/smf', 
    '/udm', '/udr', '/upf', '/bsf'
]

def read_influx_core_only(file_path):
    if not os.path.exists(file_path):
        return None
    try:

        df = pd.read_csv(file_path, comment='#', index_col=False)
        df.columns = [str(c).strip() for c in df.columns]
        
        if '_field' not in df.columns:
            return None

        df = df[df['_field'] == 'cpu_usage_percent'].copy()

        df = df[df['_measurement'].isin(CORE_NF_NAMES)]
        
        if df.empty: return None

        df['_time'] = pd.to_datetime(df['_time'], format='ISO8601', utc=True)
        df['_value'] = pd.to_numeric(df['_value'], errors='coerce')

        m_list = []
        for m in df['_measurement'].unique():
            m_sub = df[df['_measurement'] == m].set_index('_time')
            m_avg = m_sub[['_value']].resample('1s').mean().fillna(0)
            label = m.replace('/', '').upper()
            m_avg.columns = [label]
            m_list.append(m_avg)
        
        pivot = pd.concat(m_list, axis=1).fillna(0)
        pivot.index = (pivot.index - pivot.index.min()).total_seconds().astype(int)

        res = pivot.reindex(range(TIME_LIMIT + 1)).fillna(0)
        return res / num_cores
    except:
        return None

output_dir = 'core_nf_stackplots'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for delay in delays:
    for exp in experiments:

        fig, axes = plt.subplots(1, 2, figsize=(18, 8), sharey=True)

        plt.subplots_adjust(top=0.82, bottom=0.2, wspace=0.1)
        
        has_plot_data = False

        for col_idx, core in enumerate(core_info):
            ax = axes[col_idx]
            exe_results = []

            for exe in exes:
                path = base_filename.format(exe, core['id'], delay, exp)
                res = read_influx_core_only(path)
                if res is not None:
                    exe_results.append(res)
            
            if exe_results:

                final_avg = pd.concat(exe_results).groupby(level=0).mean().sort_index(axis=1)

                ax.stackplot(final_avg.index, final_avg.values.T, 
                             labels=final_avg.columns, alpha=0.85, edgecolor='white', linewidth=0.3)
                
                ax.set_title(f"{core['label']} (Avg n={len(exe_results)})", fontsize=14, fontweight='bold')
                ax.set_xlim(0, TIME_LIMIT)
                ax.set_ylim(0, 100)
                ax.set_xlabel('Time (s)', fontsize=12)
                ax.grid(True, linestyle=':', alpha=0.5)

                ax.legend(loc='upper left', bbox_to_anchor=(0, -0.15), ncol=3, fontsize=9, frameon=True)
                has_plot_data = True
            else:
                ax.set_title(f"{core['label']} (No Valid Data)")

        if has_plot_data:
            axes[0].set_ylabel('CPU Usage % (Core NFs Only)', fontsize=13)
            plt.suptitle(f"Core NF Resource Distribution | Delay: {delay}ms | gNBs: {exp}", fontsize=16, y=0.97)
            
            save_path = f"{output_dir}/Core_CPU_D{delay}_E{exp}.png"
            plt.savefig(save_path, dpi=200, bbox_inches='tight')
            plt.close()