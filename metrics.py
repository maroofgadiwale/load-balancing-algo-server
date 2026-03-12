import csv
import os
from simulation import SimulationResult


def print_comparison_table(results: list[SimulationResult]):
    col_w = 26
    num_w = 12

    algorithms = [r.algorithm_name for r in results]

    # Header
    header = f"{'Metric':<{col_w}}" + "".join(f"{a:>{num_w}}" for a in algorithms)
    sep = "-" * len(header)

    print("\n" + sep)
    print("  LOAD BALANCING ALGORITHMS — PERFORMANCE COMPARISON")
    print(sep)
    print(header)
    print(sep)

    rows = [
        ("Avg Response Time (s)", lambda r: f"{r.avg_response_time:.4f}"),
        ("Min Response Time (s)", lambda r: f"{r.min_response_time:.4f}"),
        ("Max Response Time (s)", lambda r: f"{r.max_response_time:.4f}"),
        ("Avg Processing Time (s)", lambda r: f"{r.avg_processing_time:.4f}"),
        ("Min Processing Time (s)", lambda r: f"{r.min_processing_time:.4f}"),
        ("Max Processing Time (s)", lambda r: f"{r.max_processing_time:.4f}"),
        ("Avg Wait Time (s)", lambda r: f"{r.avg_wait_time:.4f}"),
        ("Avg VM Utilization (%)", lambda r: f"{r.avg_utilization:.1f}"),
        ("Tasks Completed", lambda r: f"{r.completed_tasks}/{r.num_tasks}"),
    ]

    for label, fn in rows:
        row = f"{label:<{col_w}}" + "".join(f"{fn(r):>{num_w}}" for r in results)
        print(row)

    print(sep + "\n")

    # Per-VM breakdown
    print("  VM UTILIZATION BREAKDOWN (%)")
    print(sep)
    all_vm_ids = sorted(results[0].vm_utilizations.keys())
    vm_header = f"{'VM':<{col_w}}" + "".join(f"{a:>{num_w}}" for a in algorithms)
    print(vm_header)
    print(sep)
    for vm_id in all_vm_ids:
        row = f"{f'VM-{vm_id}':<{col_w}}" + "".join(
            f"{r.vm_utilizations.get(vm_id, 0):.1f}%".rjust(num_w)
            for r in results
        )
        print(row)
    print(sep + "\n")


# CSV export
def export_to_csv(results: list[SimulationResult], filepath: str = "results.csv"):
    """Export summary metrics for all algorithms to a CSV file."""

    fieldnames = [
        "Algorithm",
        "Tasks Completed", "Total Tasks",
        "Avg Response Time", "Min Response Time", "Max Response Time",
        "Avg Processing Time", "Min Processing Time", "Max Processing Time",
        "Avg Wait Time",
        "Avg VM Utilization",
    ]

    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            writer.writerow({
                "Algorithm": r.algorithm_name,
                "Tasks Completed": r.completed_tasks,
                "Total Tasks": r.num_tasks,
                "Avg Response Time": round(r.avg_response_time, 4),
                "Min Response Time": round(r.min_response_time, 4),
                "Max Response Time": round(r.max_response_time, 4),
                "Avg Processing Time": round(r.avg_processing_time, 4),
                "Min Processing Time": round(r.min_processing_time, 4),
                "Max Processing Time": round(r.max_processing_time, 4),
                "Avg Wait Time": round(r.avg_wait_time, 4),
                "Avg VM Utilization": round(r.avg_utilization, 2),
            })

    print(f"  ✓ Results exported to {filepath}")
