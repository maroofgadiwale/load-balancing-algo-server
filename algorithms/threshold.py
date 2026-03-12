from models import VM, Cloudlet


class ThresholdBalancer:
    name = "Threshold Based"

    def __init__(self, vms: list[VM], upper_threshold: float = 0.80):
        self.vms = vms
        self.upper_threshold = upper_threshold

    def select_vm(self, cloudlet: Cloudlet) -> VM:
        # Candidate VMs: those currently below the threshold
        available = [vm for vm in self.vms
                     if vm.utilization < self.upper_threshold]

        if available:
            return min(available, key=lambda vm: vm.current_load)

        return min(self.vms, key=lambda vm: vm.current_load)

    def reset(self):
        pass
