from models import VM, Cloudlet


class WeightedRoundRobinBalancer:
    name = "Weighted Round Robin"

    def __init__(self, vms: list[VM]):
        self.vms = vms
        self.total_weight = sum(vm.weight for vm in vms)
        self._curr_weights = {vm.vm_id: 0 for vm in vms}

    def select_vm(self, cloudlet: Cloudlet) -> VM:
        # Step 1 — Increment current vm weight with static weight
        for vm in self.vms:
            self._curr_weights[vm.vm_id] += vm.weight

        # Step 2 — Highest current weight VM
        best = max(self.vms, key=lambda vm: self._curr_weights[vm.vm_id])

        # Step 3 — Winner
        self._curr_weights[best.vm_id] -= self.total_weight

        return best

    def reset(self):
        self._curr_weights = {vm.vm_id: 0 for vm in self.vms}
