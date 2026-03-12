# Round robin algo:
from models import VM, Cloudlet


class RoundRobinBalancer:

    name = "Round Robin"

    def __init__(self, vms: list[VM]):
        self.vms = vms
        self._index = 0

    def select_vm(self, cloudlet: Cloudlet) -> VM:
        vm = self.vms[self._index]
        self._index = (self._index + 1) % len(self.vms)
        return vm

    def reset(self):
        self._index = 0
