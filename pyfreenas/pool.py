from enum import Enum, unique
from typing import TypeVar

TMachine = TypeVar("TMachine", bound="Machine")
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


class Pool(object):
    def __init__(self, machine: TMachine, guid: str) -> None:
        self._machine = machine
        self._guid = guid
        self._cached_state = self._state

    @property
    def available(self) -> bool:
        """If the pool exists on the Machine."""
        return self._guid in self._machine._state["pools"]

    @property
    def encrypt(self) -> int:
        """The encrypt? of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["encrypt"]
        return self._cached_state["encrypt"]

    @property
    def guid(self) -> str:
        """The guid of the pool."""
        return self._guid

    @property
    def id(self) -> int:
        """The id of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["id"]
        return self._cached_state["id"]

    @property
    def is_decrypted(self) -> bool:
        """Is the pool decrypted?"""
        if self.available:
            self._cached_state = self._state
            return self._state["is_decrypted"]
        return self._cached_state["is_decrypted"]

    @property
    def name(self) -> str:
        """The name of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["name"]
        return self._cached_state["name"]

    @property
    def status(self) -> PoolStatus:
        """The status of the pool."""
        if self.available:
            self._cached_state = self._state
            return PoolStatus.fromValue(self._state["status"])
        return PoolStatus.fromValue(self._cached_state["status"])

    @property
    def topology(self) -> dict:
        """The topology of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["topology"]
        return self._cached_state["topology"]

    @property
    def _state(self) -> dict:
        """The state of the pool, according to the Machine."""
        return self._machine._state["pools"][self._guid]

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.guid.__eq__(other.guid)

    def __hash__(self):
        return self.guid.__hash__()
