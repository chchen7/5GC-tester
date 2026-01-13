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

CORE_NFS = ['/amf', '/ausf', '/nrf', '/nssf', 'n3iwf', '/pcf', '/smf', '/udm', '/udr', '/upf', '/bsf']

def read_influx_csv_robust(file_path):

    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, comment='#', index_col=False)
        df.columns = [str(c).strip() for c in df.columns]
        
        if '_field' not in df.columns:
            return None

        df = df[df['_field'] == 'cpu_usage_percent'].copy()
        if df.empty: return None

        df['_time'] = pd.to_datetime(df['_time'], format='ISO8601', utc=True)
        df['_value'] = pd.to_numeric(df['_value'], errors='coerce')
        return df
    except:
        return None

output_dir = 'stackplots_0_80s'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for delay in delays:
    for exp in experiments:
        fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True)
        data_found_for_scenario = False

        for col_idx, core_id in enumerate(cores):
            ax = axes[col_idx]
            exe_summaries = [] 
            
            for exe in exes:
                path = base_filename.format(exe, core_id, delay, exp)
                cpu_df = read_influx_csv_robust(path)
                
                if cpu_df is None: continue
                
                try:
                    resampled = []
                    for m in cpu_df['_measurement'].unique():
                        m_sub = cpu_df[cpu_df['_measurement'] == m].set_index('_time')
                        m_avg = m_sub[['_value']].resample('1s').mean().fillna(0)
                        m_avg.columns = [m]
                        resampled.append(m_avg)
                    
                    if not resampled: continue
                    
                    pivot = pd.concat(resampled, axis=1).fillna(0)

                    pivot.index = (pivot.index - pivot.index.min()).total_seconds().astype(int)

                    tester_cols = [c for c in pivot.columns if 'ueransim-ueransim-gnb' in c]

                    core_cols = [c for c in pivot.columns if c in CORE_NFS]

                    other_cols = [c for c in pivot.columns if c not in tester_cols and c not in core_cols]
                    
                    summary = pd.DataFrame(index=pivot.index)
                    summary['Others'] = pivot[other_cols].sum(axis=1) / num_cores
                    summary['Core'] = pivot[core_cols].sum(axis=1) / num_cores
                    summary['Testers'] = pivot[tester_cols].sum(axis=1) / num_cores
            
                    summary = summary[summary.index <= TIME_LIMIT]
                    exe_summaries.append(summary)
                except:
                    continue


            if exe_summaries:
                final = pd.concat(exe_summaries).groupby(level=0).mean().sort_index()

                if final.index.max() < TIME_LIMIT:
                    new_idx = range(TIME_LIMIT + 1)
                    final = final.reindex(new_idx).fillna(0)

                ax.stackplot(final.index, final['Others'], final['Core'], final['Testers'], 
                             labels=['Others', 'Core', 'Testers'], 
                             colors=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.8)
                
                ax.set_title(f"{core_labels[core_id]} (n={len(exe_summaries)})", fontsize=12, fontweight='bold')
                ax.set_xlabel('Time (s)')
                ax.set_ylim(0, 100)
                ax.set_xlim(0, TIME_LIMIT) 
                ax.grid(True, linestyle=':', alpha=0.6)
                data_found_for_scenario = True
            else:
                ax.set_title(f"{core_labels[core_id]} (No Data)")

        if data_found_for_scenario:
            
            handles = [plt.Rectangle((0,0),1,1, color=c) for c in ['#1f77b4', '#ff7f0e', '#2ca02c']]
            fig.legend(handles, ['Others', 'Core', 'Testers'], loc='upper center', ncol=3, frameon=False)
            
            plt.tight_layout(rect=[0, 0.05, 1, 0.92])
            plt.savefig(f"{output_dir}/cpu_80s_D{delay}_E{exp}.png", dpi=200)
            plt.close()