from abc import abstractmethod, ABC
from enum import Enum, unique
from typing import TypeVar, Optional

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


class Disk(ABC):
    def __init__(self, serial: str) -> None:
        self._serial = serial

    @property
    @abstractmethod
    def description(self) -> str:
        """The description of the desk."""

    @property
    @abstractmethod
    def model(self) -> str:
        """The model of the disk."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the disk."""

    @property
    def serial(self) -> str:
        """The serial of the disk."""
        return self._serial

    @property
    @abstractmethod
    def size(self) -> int:
        """The size of the disk."""

    @property
    @abstractmethod
    def temperature(self) -> Optional[int]:
        """The temperature of the disk."""

    @property
    @abstractmethod
    def type(self) -> DiskType:
        """The type of the desk."""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.serial.__eq__(other.serial)

    def __hash__(self):
        return self.serial.__hash__()
