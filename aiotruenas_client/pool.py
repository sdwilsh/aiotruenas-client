from abc import abstractmethod, ABC
from enum import Enum, unique
from typing import TypeVar

TPoolStatus = TypeVar("TType", bound="PoolStatus")


@unique
class PoolStatus(Enum):
    # States from "man zpool"
    DEGRADED = "DEGRADED"
    FAULTED = "FAULTED"
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    REMOVED = "REMOVED"
    UNAVAIL = "UNAVAIL"
    # State unique to FreeNAS (AFAIK)
    # Pool known by FreeNAS, but not by zfs (I think)
    UNKNOWN = "UNKNOWN"

    @classmethod
    def fromValue(cls, value: str) -> TPoolStatus:
        if value == cls.DEGRADED.value:
            return cls.DEGRADED
        if value == cls.FAULTED.value:
            return cls.FAULTED
        if value == cls.OFFLINE.value:
            return cls.OFFLINE
        if value == cls.ONLINE.value:
            return cls.ONLINE
        if value == cls.REMOVED.value:
            return cls.REMOVED
        if value == cls.UNAVAIL.value:
            return cls.UNAVAIL
        if value == cls.UNKNOWN.value:
            return cls.UNKNOWN
        raise Exception(f"Unexpected pool status '{value}'")


class Pool(ABC):
    def __init__(self, guid: str) -> None:
        self._guid = guid

    @property
    @abstractmethod
    def encrypt(self) -> int:
        """The encrypt? of the pool."""

    @property
    def guid(self) -> str:
        """The guid of the pool."""
        return self._guid

    @property
    @abstractmethod
    def id(self) -> int:
        """The id of the pool."""

    @property
    @abstractmethod
    def is_decrypted(self) -> bool:
        """Is the pool decrypted?"""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the pool."""

    @property
    @abstractmethod
    def status(self) -> PoolStatus:
        """The status of the pool."""

    @property
    @abstractmethod
    def topology(self) -> dict:
        """The topology of the pool."""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.guid.__eq__(other.guid)

    def __hash__(self):
        return self.guid.__hash__()
