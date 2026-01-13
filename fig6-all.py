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

core_labels = {0: 'free5GC', 1: 'Open5GS'}

CORE_NF_NAMES = [
    '/amf', '/ausf', '/nrf', '/nssf', '/pcf', '/smf', 
    '/udm', '/udr', '/upf', '/bsf'
]

def get_avg_nf_usage(file_path):

    if not os.path.exists(file_path): return None
    try:
        df = pd.read_csv(file_path, comment='#', index_col=False)
        df.columns = [str(c).strip() for c in df.columns]
        df = df[df['_field'] == 'cpu_usage_percent']
        df = df[df['_measurement'].isin(CORE_NF_NAMES)].copy()
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

        pivot = pivot[(pivot.index >= 0) & (pivot.index <= TIME_LIMIT)]

        return pivot.mean() / num_cores
    except:
        return None

results = []


for core_id in cores:
    for delay in delays:
        for exp in experiments:
            exe_data_list = []
            for exe in exes:
                path = base_filename.format(exe, core_id, delay, exp)
                nf_usage = get_avg_nf_usage(path)
                if nf_usage is not None:
                    exe_data_list.append(nf_usage)
            
            if exe_data_list:

                final_nf_avg = pd.concat(exe_data_list, axis=1).mean(axis=1)

                row = {
                    'Core': core_labels[core_id],
                    'Delay': delay,
                    'gNB_Count': exp,
                    'Samples': len(exe_data_list)
                }
                row.update(final_nf_avg.to_dict())
                results.append(row)

summary_df = pd.DataFrame(results).fillna(0)
summary_df.to_csv('all_scenarios_nf_breakdown.csv', index=False)

fig, axes = plt.subplots(len(cores), len(delays), figsize=(25, 12), sharey=True)

all_nfs = [c for c in summary_df.columns if c not in ['Core', 'Delay', 'gNB_Count', 'Samples']]

for r, core_name in enumerate(['free5GC', 'Open5GS']):
    for c, delay in enumerate(delays):
        ax = axes[r, c]
        subset = summary_df[(summary_df['Core'] == core_name) & (summary_df['Delay'] == delay)]
        subset = subset.sort_values('gNB_Count')
        
        if not subset.empty:
            x = subset['gNB_Count']
            y_stacks = [subset[nf] for nf in all_nfs]
            
            ax.stackplot(x, y_stacks, labels=all_nfs, alpha=0.8)
            
            ax.set_title(f"{core_name} | {delay}ms", fontsize=12, fontweight='bold')
            ax.set_xticks(experiments)
            if r == 1: ax.set_xlabel("gNB Count")
            if c == 0: ax.set_ylabel("Avg CPU Load (%)")
            ax.grid(True, linestyle=':', alpha=0.6)
        else:
            ax.set_title(f"{core_name} | {delay}ms (No Data)")

handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=len(all_nfs)//2 + 1, bbox_to_anchor=(0.5, 0.02), fontsize=10)

plt.suptitle("Individual NF Resource Consumption Trend Across All Scenarios (0-80s Avg)", fontsize=20, y=0.98)
plt.tight_layout(rect=[0, 0.08, 1, 0.95])
plt.savefig('all_scenarios_nf_stackplot.png', dpi=300)