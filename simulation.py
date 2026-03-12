import simpy
import random
import statistics
from dataclasses import dataclass, field
from models import VM, Cloudlet, Datacenter


# Result container
@dataclass
class SimulationResult:
    algorithm_name: str
    num_tasks: int
    completed_tasks: int

    # Response time  = arrival → finish
    avg_response_time: float
    min_response_time: float
    max_response_time: float

    # Processing time = start  → finish
    avg_processing_time: float
    min_processing_time: float
    max_processing_time: float

    # Wait time       = arrival → start
    avg_wait_time: float

    # Per-VM utilisation
    vm_utilizations: dict = field(default_factory=dict)  # vm_id → %
    avg_utilization: float = 0.0

    # Raw cloudlets (for detailed analysis)
    cloudlets: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"\n{'=' * 60}",
            f"  Algorithm : {self.algorithm_name}",
            f"  Tasks     : {self.completed_tasks}/{self.num_tasks} completed",
            f"{'=' * 60}",
            f"  Avg Response Time  : {self.avg_response_time:.4f} s",
            f"  Min Response Time  : {self.min_response_time:.4f} s",
            f"  Max Response Time  : {self.max_response_time:.4f} s",
            f"  Avg Processing Time: {self.avg_processing_time:.4f} s",
            f"  Avg Wait Time      : {self.avg_wait_time:.4f} s",
            f"  Avg VM Utilization : {self.avg_utilization:.1f}%",
            f"{'=' * 60}",
        ]
        for vm_id, util in self.vm_utilizations.items():
            lines.append(f"    VM-{vm_id} utilization: {util:.1f}%")
        lines.append("")
        return "\n".join(lines)


# SimPy process: process one cloudlet on its assigned VM
def _process_cloudlet(env: simpy.Environment, cloudlet: Cloudlet, vm: VM):

    vm.current_load += 1

    with vm.resource.request() as req:
        yield req  # wait for a free slot

        cloudlet.start_time = env.now  # execution starts
        exec_time = cloudlet.length / vm.mips  # t = MI / MIPS

        yield env.timeout(exec_time)  # simulate execution

        cloudlet.finish_time = env.now  # execution ends

    vm.current_load -= 1
    vm.total_tasks_processed += 1
    vm.total_busy_time += cloudlet.processing_time


def _generate_cloudlets(
        env: simpy.Environment,
        balancer,
        datacenter: Datacenter,
        num_tasks: int,
        avg_arrival_rate: float,
        min_length: float,
        max_length: float,
        completed: list,
        rng: random.Random,
):

    mean_interarrival = 1.0 / avg_arrival_rate

    for i in range(num_tasks):
        # Poisson inter-arrival  →  exponential gaps
        gap = rng.expovariate(1.0 / mean_interarrival)
        yield env.timeout(gap)

        # Create cloudlet with random length
        length = rng.uniform(min_length, max_length)

        # fixed_lengths = [1000.0, 2000.0, 3000.0]
        # length = fixed_lengths[i % len(fixed_lengths)]

        cloudlet = Cloudlet(cloudlet_id=i, length=length, arrival_time=env.now)

        # Load balancer picks a VM
        vm = balancer.select_vm(cloudlet)
        cloudlet.assigned_vm = vm.vm_id

        # Spawn async process (non-blocking)
        env.process(_process_cloudlet(env, cloudlet, vm))
        completed.append(cloudlet)


def run_simulation(
        balancer,
        vms: list[VM],
        num_tasks: int = 500,
        avg_arrival_rate: float = 10.0,  # tasks per second
        min_task_length: float = 100.0,  # MI
        max_task_length: float = 1000.0,  # MI
        sim_duration: float = None,  # None = run until all tasks arrive
        seed: int = 42,
) -> SimulationResult:
    rng = random.Random(seed)

    # --- Reset VM state so each algorithm starts fresh ---
    env = simpy.Environment()
    dc = Datacenter(dc_id=1, vms=vms)
    dc.setup(env)

    for vm in vms:
        vm.total_tasks_processed = 0
        vm.total_busy_time = 0.0
        vm.current_load = 0

    balancer.reset()

    # --- Track all generated cloudlets ---
    cloudlets: list[Cloudlet] = []

    # --- Schedule the generator process ---
    env.process(
        _generate_cloudlets(
            env, balancer, dc,
            num_tasks, avg_arrival_rate,
            min_task_length, max_task_length,
            cloudlets, rng,
        )
    )

    # --- Calculate sim_duration if not provided ---
    if sim_duration is None:
        expected_arrival_window = num_tasks / avg_arrival_rate
        avg_exec = ((min_task_length + max_task_length) / 2) / min(vm.mips for vm in vms)
        sim_duration = expected_arrival_window + avg_exec * 5

    env.run(until=sim_duration)

    # --- Collect metrics from finished cloudlets ---
    finished = [c for c in cloudlets if c.finish_time is not None]

    if not finished:
        raise RuntimeError("No cloudlets completed — increase sim_duration or check VM MIPS.")

    response_times = [c.response_time for c in finished]
    processing_times = [c.processing_time for c in finished]
    wait_times = [c.wait_time for c in finished]

    # Per-VM utilisation snapshot (busy_time / total_sim_time × 100)
    vm_utils = {}
    for vm in vms:
        util = (vm.total_busy_time / sim_duration) * 100
        vm_utils[vm.vm_id] = round(min(util, 100.0), 2)

    return SimulationResult(
        algorithm_name=balancer.name,
        num_tasks=num_tasks,
        completed_tasks=len(finished),
        avg_response_time=statistics.mean(response_times),
        min_response_time=min(response_times),
        max_response_time=max(response_times),
        avg_processing_time=statistics.mean(processing_times),
        min_processing_time=min(processing_times),
        max_processing_time=max(processing_times),
        avg_wait_time=statistics.mean(wait_times),
        vm_utilizations=vm_utils,
        avg_utilization=statistics.mean(vm_utils.values()),
        cloudlets=finished,
    )
