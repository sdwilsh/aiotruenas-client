from enum import Enum, unique
from typing import TypeVar

TMachine = TypeVar("TMachine", bound="Machine")
TType = TypeVar("TType", bound="DiskType")


@unique
class DiskType(Enum):
    HDD = "HDD"
    SSD = "SSD"

    @classmethod
    def fromValue(cls, value: str) -> TType:
        if value == cls.HDD.value:
            return cls.HDD
        if value == cls.SSD.value:
            return cls.SSD
        raise Exception(f"Unexpected disk type '{value}'")


class Disk(object):
    def __init__(self, machine: TMachine, serial: str) -> None:
        self._machine = machine
        self._serial = serial
        self._cached_state = self._state

    @property
    def available(self) -> bool:
        """If the disk exists on the server."""
        return self._serial in self._machine._state["disks"]

    @property
    def description(self) -> str:
        """The description of the desk."""
        if self.available:
            self._cached_state = self._state
            return self._state["description"]
        return self._cached_state["description"]

    @property
    def model(self) -> str:
        """The model of the disk."""
        if self.available:
            self._cached_state = self._state
            return self._state["model"]
        return self._cached_state["model"]

    @property
    def name(self) -> str:
        """The name of the disk."""
        if self.available:
            self._cached_state = self._state
            return self._state["name"]
        return self._cached_state["name"]

    @property
    def serial(self) -> str:
        """The serial of the disk."""
        return self._serial

    @property
    def size(self) -> int:
        """The size of the disk."""
        if self.available:
            self._cached_state = self._state
            return self._state["size"]
        return self._cached_state["size"]

    @property
    def temperature(self) -> int:
        """The temperature of the disk."""
        assert self.available
        return self._state["temperature"]

    @property
    def type(self) -> DiskType:
        """The type of the desk."""
        if self.available:
            self._cached_state = self._state
            return DiskType.fromValue(self._state["type"])
        return DiskType.fromValue(self._cached_state["type"])

    @property
    def _state(self) -> dict:
        """The state of the desk, according to the Machine."""
        return self._machine._state["disks"][self._serial]

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.serial.__eq__(other.serial)

    def __hash__(self):
        return self.serial.__hash__()
