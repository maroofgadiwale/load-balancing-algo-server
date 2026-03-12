# Program to implement Load Balancing:
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from models import VM
from simulation import run_simulation
from metrics import print_comparison_table, export_to_csv
from visualize import generate_all_charts

from algorithms.round_robin import RoundRobinBalancer
from algorithms.weighted_rr import WeightedRoundRobinBalancer
from algorithms.threshold import ThresholdBalancer
from algorithms.honeybee import HoneyBeeBalancer
from algorithms.aco import ACOBalancer


# Virtual Machines: (vm_id, mips, capacity, weight)
VM_CONFIGS = [
    (1, 1000, 8, 1),  # slow  VM
    (2, 2000, 8, 2),
    (3, 3000, 8, 3),  # fast  VM
    (4, 1500, 8, 2),
    (5, 2500, 8, 2),
]

NUM_TASKS = 1000
AVG_ARRIVAL_RATE = 20.0
MIN_TASK_LENGTH = 200.0
MAX_TASK_LENGTH = 2000.0
SEED = 42


OUTPUT_DIR = "output"
CSV_FILE = os.path.join(OUTPUT_DIR, "results.csv")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")

# Helper function:
def build_vms() -> list[VM]:
    return [VM(vm_id=cfg[0], mips=cfg[1], capacity=cfg[2], weight=cfg[3])
            for cfg in VM_CONFIGS]


# Main function:
def main():
    print("\n" + "=" * 60)
    print("  Cloud Load Balancing Simulation (SimPy)")
    print("=" * 60)
    print(f"  VMs          : {len(VM_CONFIGS)}")
    print(f"  Tasks        : {NUM_TASKS}")
    print(f"  Arrival rate : {AVG_ARRIVAL_RATE} tasks/s")
    print(f"  Task length  : {MIN_TASK_LENGTH}–{MAX_TASK_LENGTH} MI")
    print(f"  Seed         : {SEED}")
    print("=" * 60)

    algorithms = [
        ("Round Robin", lambda vms: RoundRobinBalancer(vms)),
        ("Weighted Round Robin", lambda vms: WeightedRoundRobinBalancer(vms)),
        ("Threshold Based", lambda vms: ThresholdBalancer(vms, upper_threshold=0.80)),
        ("Honey Bee Foraging", lambda vms: HoneyBeeBalancer(vms, abandon_limit=5)),
        ("Ant Colony Optimization", lambda vms: ACOBalancer(vms, alpha=1.0, beta=2.0, rho=0.1, q=100)),
    ]

    results = []

    for algo_name, make_balancer in algorithms:
        print(f"\n  Running: {algo_name} ...", end="", flush=True)
        vms = build_vms()
        balancer = make_balancer(vms)

        result = run_simulation(
            balancer=balancer,
            vms=vms,
            num_tasks=NUM_TASKS,
            avg_arrival_rate=AVG_ARRIVAL_RATE,
            min_task_length=MIN_TASK_LENGTH,
            max_task_length=MAX_TASK_LENGTH,
            seed=SEED,
        )
        results.append(result)
        print(f" done  [avg_rt={result.avg_response_time:.4f}s]")

    # Console table
    print_comparison_table(results)

    # CSV
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    export_to_csv(results, CSV_FILE)

    # Charts
    try:
        generate_all_charts(results, CHARTS_DIR)
    except ImportError:
        print("Error")

    print("\n  All done! Outputs Saved!\n")


if __name__ == "__main__":
    main()
