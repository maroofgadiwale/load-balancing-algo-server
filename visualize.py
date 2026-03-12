import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import os
from simulation import SimulationResult



COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63", "#9C27B0"]


def _save(fig, path: str):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  ✓ Saved {path}")


# 1. Avg Response Time bar chart
def plot_avg_response_time(results: list[SimulationResult], out_dir: str = "."):
    names  = [r.algorithm_name for r in results]
    values = [r.avg_response_time for r in results]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(names, values, color=COLORS[:len(results)], edgecolor="white", width=0.5)

    ax.set_title("Average Response Time by Algorithm", fontsize=14, fontweight="bold")
    ax.set_ylabel("Time (seconds)")
    ax.set_xlabel("Algorithm")
    ax.bar_label(bars, fmt="%.4f", padding=3, fontsize=9)
    ax.set_ylim(0, max(values) * 1.2)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    _save(fig, os.path.join(out_dir, "1_avg_response_time.png"))


# 2. Avg Processing Time bar chart
def plot_avg_processing_time(results: list[SimulationResult], out_dir: str = "."):
    names  = [r.algorithm_name for r in results]
    values = [r.avg_processing_time for r in results]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(names, values, color=COLORS[:len(results)], edgecolor="white", width=0.5)

    ax.set_title("Average Processing Time by Algorithm", fontsize=14, fontweight="bold")
    ax.set_ylabel("Time (seconds)")
    ax.set_xlabel("Algorithm")
    ax.bar_label(bars, fmt="%.4f", padding=3, fontsize=9)
    ax.set_ylim(0, max(values) * 1.2)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    _save(fig, os.path.join(out_dir, "2_avg_processing_time.png"))


# 3. Avg VM Utilization bar chart
def plot_avg_utilization(results: list[SimulationResult], out_dir: str = "."):
    names  = [r.algorithm_name for r in results]
    values = [r.avg_utilization for r in results]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(names, values, color=COLORS[:len(results)], edgecolor="white", width=0.5)

    ax.set_title("Average VM Utilization by Algorithm", fontsize=14, fontweight="bold")
    ax.set_ylabel("Utilization (%)")
    ax.set_xlabel("Algorithm")
    ax.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=9)
    ax.set_ylim(0, 110)
    ax.axhline(y=80, color="red", linestyle="--", linewidth=1, label="80% threshold")
    ax.legend()
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    _save(fig, os.path.join(out_dir, "3_avg_utilization.png"))


# 4. Min / Avg / Max Response Time grouped bar
def plot_response_time_range(results: list[SimulationResult], out_dir: str = "."):
    names   = [r.algorithm_name for r in results]
    mins    = [r.min_response_time for r in results]
    avgs    = [r.avg_response_time for r in results]
    maxs    = [r.max_response_time for r in results]

    x      = np.arange(len(names))
    width  = 0.25

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - width, mins, width, label="Min",  color="#64B5F6", edgecolor="white")
    ax.bar(x,         avgs, width, label="Avg",  color="#1976D2", edgecolor="white")
    ax.bar(x + width, maxs, width, label="Max",  color="#0D47A1", edgecolor="white")

    ax.set_title("Response Time Range (Min / Avg / Max)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Time (seconds)")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.legend()
    plt.tight_layout()
    _save(fig, os.path.join(out_dir, "4_response_time_range.png"))



# 5. Per-VM utilisation heatmap
def plot_vm_utilization_heatmap(results: list[SimulationResult], out_dir: str = "."):
    algo_names = [r.algorithm_name for r in results]
    vm_ids     = sorted(results[0].vm_utilizations.keys())

    # Build matrix: rows=VMs, cols=algorithms
    matrix = np.array([
        [r.vm_utilizations.get(vm_id, 0) for r in results]
        for vm_id in vm_ids
    ])

    fig, ax = plt.subplots(figsize=(11, max(4, len(vm_ids) * 0.7)))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)

    ax.set_xticks(range(len(algo_names)))
    ax.set_xticklabels(algo_names, rotation=20, ha="right")
    ax.set_yticks(range(len(vm_ids)))
    ax.set_yticklabels([f"VM-{vid}" for vid in vm_ids])
    ax.set_title("VM Utilization Heatmap (%)", fontsize=14, fontweight="bold")

    # Annotate cells
    for i in range(len(vm_ids)):
        for j in range(len(algo_names)):
            ax.text(j, i, f"{matrix[i, j]:.1f}%",
                    ha="center", va="center",
                    color="black" if matrix[i, j] < 60 else "white",
                    fontsize=8)

    plt.colorbar(im, ax=ax, label="Utilization (%)")
    plt.tight_layout()
    _save(fig, os.path.join(out_dir, "5_vm_utilization_heatmap.png"))


# 6. Response time distribution (sorted) — CDF-like line
def plot_response_time_distribution(results: list[SimulationResult], out_dir: str = "."):
    fig, ax = plt.subplots(figsize=(11, 5))

    for idx, r in enumerate(results):
        rt_sorted = sorted(c.response_time for c in r.cloudlets if c.response_time)
        cdf_y     = np.linspace(0, 100, len(rt_sorted))
        ax.plot(rt_sorted, cdf_y, label=r.algorithm_name,
                color=COLORS[idx % len(COLORS)], linewidth=2)

    ax.set_title("Response Time CDF (Cumulative Distribution)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Response Time (seconds)")
    ax.set_ylabel("% of Tasks Completed")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, os.path.join(out_dir, "6_response_time_cdf.png"))


# Master function: generate all charts
def generate_all_charts(results: list[SimulationResult], out_dir: str = "charts"):
    print(f"\n  Generating charts → {out_dir}/")
    plot_avg_response_time(results, out_dir)
    plot_avg_processing_time(results, out_dir)
    plot_avg_utilization(results, out_dir)
    plot_response_time_range(results, out_dir)
    plot_vm_utilization_heatmap(results, out_dir)
    plot_response_time_distribution(results, out_dir)
    print()
