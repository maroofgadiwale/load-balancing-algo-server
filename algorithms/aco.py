import math
import random
from models import VM, Cloudlet


class ACOBalancer:
    name = "Ant Colony Optimization"

    def __init__(
            self,
            vms: list[VM],
            alpha: float = 1.0,
            beta: float = 2.0,
            rho: float = 0.1,
            q: float = 100.0,
    ):
        self.vms = vms
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.q = q

        # Pheromone
        self._pheromone: dict[int, float] = {vm.vm_id: 1.0 for vm in vms}

    # Heuristic:
    def _heuristic(self, vm: VM) -> float:
        free = max(1, vm.capacity - vm.current_load)
        return free / vm.capacity

    # Core selection
    def select_vm(self, cloudlet: Cloudlet) -> VM:
        for vm in self.vms:
            self._pheromone[vm.vm_id] = max(
                0.01,
                (1 - self.rho) * self._pheromone[vm.vm_id]
            )

        # Compute attractiveness scores
        scores = []
        for vm in self.vms:
            tau = self._pheromone[vm.vm_id] ** self.alpha
            eta = self._heuristic(vm) ** self.beta
            scores.append(tau * eta)

        total = sum(scores)
        probabilities = [s / total for s in scores]

        chosen = random.choices(self.vms, weights=probabilities, k=1)[0]

        deposit = self.q * self._heuristic(chosen)
        self._pheromone[chosen.vm_id] += deposit

        return chosen

    def reset(self):
        self._pheromone = {vm.vm_id: 1.0 for vm in self.vms}
