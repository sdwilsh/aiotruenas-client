from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .disk import Disk
from .jail import Jail
from .job import Job, TJobId
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

    async def get_jails(self) -> List[Jail]:
        """Get the jails on the remote machine."""

    @abstractmethod
    async def get_job(self, id: TJobId) -> Job:
        """Get the specified Job from the remote machine."""

    @abstractmethod
    async def get_system_info(self) -> Dict[str, Any]:
        """Get some basic information about the remote machine."""

    @abstractmethod
    async def get_pools(self) -> List[Pool]:
        """Get the pools on the remote machine."""

    @abstractmethod
    async def get_vms(self) -> List[VirtualMachine]:
        """Get the disks on the remote machine."""
