import simpy
from dataclasses import dataclass, field
from typing import Optional


class VM:

    def __init__(self, vm_id: int, mips: int, capacity: int = 10, weight: int = 1):
        self.vm_id = vm_id
        self.mips = mips  # processing power
        self.capacity = capacity  # max queue depth
        self.weight = weight  # for weighted algorithms

        # Runtime state (set when env is injected)
        self.env: Optional[simpy.Environment] = None
        self.resource: Optional[simpy.Resource] = None

        # Metrics
        self.total_tasks_processed: int = 0
        self.total_busy_time: float = 0.0
        self.current_load: int = 0  # tasks currently assigned

    def setup(self, env: simpy.Environment):

        self.env = env
        self.resource = simpy.Resource(env, capacity=self.capacity)

    @property
    def utilization(self) -> float:

        if self.resource is None:
            return 0.0
        return self.resource.count / self.capacity

    @property
    def queue_length(self) -> int:

        if self.resource is None:
            return 0
        return len(self.resource.queue)

    def __repr__(self):
        return f"VM(id={self.vm_id}, mips={self.mips}, weight={self.weight})"


# ---------------------------------------------------------------------------
# Cloudlet
# ---------------------------------------------------------------------------
@dataclass
class Cloudlet:
    cloudlet_id: int
    length: float  # MI
    arrival_time: float = 0.0

    # Set during simulation
    assigned_vm: Optional[int] = field(default=None, repr=False)
    start_time: Optional[float] = field(default=None, repr=False)
    finish_time: Optional[float] = field(default=None, repr=False)

    @property
    def response_time(self) -> Optional[float]:
        if self.finish_time is not None:
            return self.finish_time - self.arrival_time
        return None

    @property
    def processing_time(self) -> Optional[float]:
        if self.start_time is not None and self.finish_time is not None:
            return self.finish_time - self.start_time
        return None

    @property
    def wait_time(self) -> Optional[float]:
        if self.start_time is not None:
            return self.start_time - self.arrival_time
        return None


# Datacenter
class Datacenter:
    def __init__(self, dc_id: int, vms: list[VM]):
        self.dc_id = dc_id
        self.vms = vms

    def setup(self, env: simpy.Environment):
        for vm in self.vms:
            vm.setup(env)

    def get_vm(self, vm_id: int) -> Optional[VM]:
        for vm in self.vms:
            if vm.vm_id == vm_id:
                return vm
        return None

    @property
    def total_load(self) -> int:
        return sum(vm.current_load for vm in self.vms)

    @property
    def avg_utilization(self) -> float:
        return sum(vm.utilization for vm in self.vms) / len(self.vms)

    def __repr__(self):
        return f"Datacenter(id={self.dc_id}, vms={len(self.vms)})"
