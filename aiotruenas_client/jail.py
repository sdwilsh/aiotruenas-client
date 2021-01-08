from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, unique


@unique
class JailStatus(Enum):
    DOWN = "down"
    UP = "up"

    @classmethod
    def fromValue(cls, value: str) -> JailStatus:
        if value == cls.DOWN.value:
            return cls.DOWN
        if value == cls.UP.value:
            return cls.UP
        raise AssertionError(f"Unexpected jail state '{value}'")


class Jail(ABC):
    _name: str

    def __init__(self, name: str) -> None:
        self._name = name

    @abstractmethod
    async def start(self, overcommit: bool = False) -> bool:
        """Starts a stopped jail."""

    @abstractmethod
    async def stop(self, force: bool = False) -> bool:
        """Stops a running jail."""

    @abstractmethod
    async def restart(self) -> bool:
        """Restarts a running jail."""

    @property
    def name(self) -> str:
        """The name of the jail."""
        return self._name

    @property
    @abstractmethod
    def status(self) -> JailStatus:
        """The status of the jail."""

    @property
    @abstractmethod
    def _state(self) -> dict:
        """The state of the jail, according to the Machine."""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.name.__eq__(other.name)

    def __hash__(self):
        return self.name.__hash__()
