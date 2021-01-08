from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, unique


@unique
class VirtualMachineState(Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"

    @classmethod
    def fromValue(cls, value: str) -> VirtualMachineState:
        if value == cls.STOPPED.value:
            return cls.STOPPED
        if value == cls.RUNNING.value:
            return cls.RUNNING
        raise Exception(f"Unexpected virtual machine state '{value}'")


class VirtualMachine(ABC):
    def __init__(self, id: int) -> None:
        self._id = id

    @abstractmethod
    async def start(self, overcommit: bool = False) -> bool:
        """Starts a stopped virtual machine."""

    @abstractmethod
    async def stop(self, force: bool = False) -> bool:
        """Stops a running virtual machine."""

    @abstractmethod
    async def restart(self) -> bool:
        """Restarts a running virtual machine."""

    @property
    @abstractmethod
    def description(self) -> str:
        """The description of the virtual machine."""

    @property
    def id(self) -> int:
        """The id of the virtual machine."""
        return self._id

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the virtual machine."""

    @property
    @abstractmethod
    def status(self) -> VirtualMachineState:
        """The status of the virtual machine."""

    @property
    @abstractmethod
    def _state(self) -> dict:
        """The state of the virtual machine, according to the Machine."""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.id.__eq__(other.id)

    def __hash__(self):
        return self.id.__hash__()
