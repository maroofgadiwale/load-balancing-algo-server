import random
from models import VM, Cloudlet


class HoneyBeeBalancer:
    name = "Honey Bee Foraging"

    def __init__(self, vms: list[VM], abandon_limit: int = 5):
        self.vms = vms
        self.abandon_limit = abandon_limit

        self._assign_streak: dict[int, int] = {vm.vm_id: 0 for vm in vms}

        self._abandoned: set[int] = set()

    def _nectar(self, vm: VM) -> float:
        free = max(0, vm.capacity - vm.current_load)
        if vm.vm_id in self._abandoned:
            return free * 0.1
        return float(free) + 1e-6

    def select_vm(self, cloudlet: Cloudlet) -> VM:
        nectars = [self._nectar(vm) for vm in self.vms]
        total = sum(nectars)
        probabilities = [n / total for n in nectars]

        # Weighted random selection
        chosen = random.choices(self.vms, weights=probabilities, k=1)[0]

        # Update streak & abandonment
        for vm in self.vms:
            if vm.vm_id == chosen.vm_id:
                self._assign_streak[vm.vm_id] += 1
                if self._assign_streak[vm.vm_id] >= self.abandon_limit:
                    self._abandoned.add(vm.vm_id)
                    self._assign_streak[vm.vm_id] = 0
            else:
                self._assign_streak[vm.vm_id] = max(
                    0, self._assign_streak[vm.vm_id] - 1
                )
                if vm.vm_id in self._abandoned and self._assign_streak[vm.vm_id] == 0:
                    self._abandoned.discard(vm.vm_id)

        return chosen

    def reset(self):
        self._assign_streak = {vm.vm_id: 0 for vm in self.vms}
        self._abandoned.clear()
