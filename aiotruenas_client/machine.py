from abc import abstractmethod, ABC
from typing import List
from .disk import Disk
from .pool import Pool
from .virtualmachine import VirtualMachine


class Machine(ABC):
    @staticmethod
    @abstractmethod
    async def create():
        """Create and validate authentication with the concrete implementation of this class."""

    @abstractmethod
    async def get_disks(self, include_temperature: bool) -> List[Disk]:
        """Get the disks on the remote machine."""

    @abstractmethod
    async def get_pools(self) -> List[Pool]:
        """Get the pools on the remote machine."""

    @abstractmethod
    async def get_vms(self) -> List[VirtualMachine]:
        """Get the disks on the remote machine."""
