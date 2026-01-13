import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

base_filename = 'result-logs-influxdb-{}-{}-{}-{}.csv' # {exe}-{core}-{delay}-{exp}
exes = range(1, 11)           
cores = [0, 1]                     # 0: free5GC, 1: Open5GS
delays = [500, 400, 300, 200, 100]
experiments = [1, 3, 5, 7, 9, 11] 
num_cores = 8                     
TIME_LIMIT = 100                   

core_labels = {0: 'free5GC', 1: 'Open5GS'}
CORE_NFS = ['/amf', '/ausf', '/nrf', '/nssf', 'n3iwf', '/pcf', '/smf', '/udm', '/udr', '/upf', '/bsf']

def read_influx_csv_robust(file_path):
    if not os.path.exists(file_path): return None
    try:
        df = pd.read_csv(file_path, comment='#', index_col=False)
        df.columns = [str(c).strip() for c in df.columns]
        if '_field' not in df.columns: return None

        df = df[df['_field'] == 'cpu_usage_percent'].copy()
        if df.empty: return None

        df['_time'] = pd.to_datetime(df['_time'], format='ISO8601', utc=True)
        df['_value'] = pd.to_numeric(df['_value'], errors='coerce')
        return df
    except:
        return None

results_list = []


for core_id in cores:
    for delay in delays:
        for exp in experiments:
            scenario_exe_data = [] 
            
            for exe in exes:
                path = base_filename.format(exe, core_id, delay, exp)
                df = read_influx_csv_robust(path)
                
                if df is None: continue 
                
                try:
                    m_list = []
                    for m in df['_measurement'].unique():
                        m_sub = df[df['_measurement'] == m].set_index('_time')
                        m_avg = m_sub[['_value']].resample('1s').mean().fillna(0).rename(columns={'_value': m})
                        m_list.append(m_avg)
                    
                    pivot = pd.concat(m_list, axis=1).fillna(0)
                    pivot.index = (pivot.index - pivot.index.min()).total_seconds().astype(int)
                    
                    pivot = pivot[(pivot.index >= 0) & (pivot.index <= TIME_LIMIT)]
                    
                    tester_cols = [c for c in pivot.columns if 'ueransim-ueransim-gnb' in c]
                    core_cols = [c for c in pivot.columns if c in CORE_NFS]
                    others_cols = [c for c in pivot.columns if c not in tester_cols and c not in core_cols]
                    
                    cat_averages = {
                        'Core': (pivot[core_cols].sum(axis=1).mean()) / num_cores,
                        'Testers': (pivot[tester_cols].sum(axis=1).mean()) / num_cores,
                        'Others': (pivot[others_cols].sum(axis=1).mean()) / num_cores
                    }
                    scenario_exe_data.append(cat_averages)
                except:
                    continue

            if scenario_exe_data:
                avg_scenario = pd.DataFrame(scenario_exe_data).mean()
                results_list.append({
                    'Core_Name': core_labels[core_id],
                    'Delay': delay,
                    'gNB_Count': exp,
                    'CPU_Core': avg_scenario['Core'],
                    'CPU_Testers': avg_scenario['Testers'],
                    'CPU_Others': avg_scenario['Others'],
                    'Total_CPU_Load': avg_scenario.sum(),
                    'Samples': len(scenario_exe_data)
                })


summary_df = pd.DataFrame(results_list)

fig, axes = plt.subplots(1, len(delays), figsize=(22, 6), sharey=True)

for i, delay in enumerate(delays):
    ax = axes[i]
    for core_name in summary_df['Core_Name'].unique():
        subset = summary_df[(summary_df['Core_Name'] == core_name) & (summary_df['Delay'] == delay)]
        subset = subset.sort_values('gNB_Count')
        
        ax.plot(subset['gNB_Count'], subset['Total_CPU_Load'], marker='o', linewidth=2, markersize=8, label=core_name)
        
    ax.set_title(f"Injection Delay: {delay}ms", fontsize=14, fontweight='bold')
    ax.set_xlabel("Number of gNBs", fontsize=12)
    ax.set_xticks(experiments)
    if i == 0: 
        ax.set_ylabel("Avg Total CPU Load (%)", fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_ylim(0, 105)

plt.suptitle(f"Total System CPU Load Scaling Trend (Averaged over 0-{TIME_LIMIT}s)", fontsize=18, y=1.02)
plt.tight_layout()
plt.savefig(f'resource_scaling_trend_0_{TIME_LIMIT}s.png', dpi=300, bbox_inches='tight')