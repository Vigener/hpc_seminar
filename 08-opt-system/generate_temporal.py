import matplotlib
matplotlib.use("Agg")
import japanize_matplotlib
import matplotlib.pyplot as plt

# Data
procs = [1, 2, 4, 8, 16, 32, 64, 112]
original_time = [0.005570, 0.002823, 0.001533, 0.000774, 0.000391, 0.000255, 0.000155, 0.000110]
temporal_time = [0.005800, 0.003000, 0.001700, 0.000900, 0.000550, 0.000450, 0.000350, 0.000300]

original_speedup = [original_time[0] / t for t in original_time]
temporal_speedup = [original_time[0] / t for t in temporal_time]

# Plot absolute time
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(procs, original_time, marker='o', label='オリジナル', linewidth=2, color='#1f77b4')
ax.plot(procs, temporal_time, marker='s', label='テンポラルブロッキング', linewidth=2, color='#ff7f0e')
ax.set_title('Laplace 2D: 1反復あたりの絶対実行時間')
ax.set_xlabel('MPI プロセス数')
ax.set_ylabel('実行時間 [秒]')
ax.set_xscale('log', base=2)
ax.set_yscale('log')
ax.set_xticks(procs)
ax.set_xticklabels(procs)
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend()
fig.savefig('../../images/temporal_time.png', bbox_inches='tight')
plt.close(fig)

# Plot speedup
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(procs, original_speedup, marker='o', label='オリジナル', linewidth=2, color='#1f77b4')
ax.plot(procs, temporal_speedup, marker='s', label='テンポラルブロッキング', linewidth=2, color='#ff7f0e')
ax.plot(procs, procs, linestyle=':', color='black', label='理想的加速 (Ideal)')
ax.set_title('Laplace 2D: テンポラルブロッキングによる加速比')
ax.set_xlabel('MPI プロセス数')
ax.set_ylabel('加速比 (Speedup)')
ax.set_xscale('log', base=2)
ax.set_yscale('log', base=2)
ax.set_xticks(procs)
ax.set_xticklabels(procs)
ax.grid(True, linestyle='--', alpha=0.6)
ax.legend()
fig.savefig('../../images/temporal_time_speedup.png', bbox_inches='tight')
plt.close(fig)
