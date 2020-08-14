from enum import Enum, unique
from typing import TypeVar

TMachine = TypeVar("TMachine", bound="Machine")
TType = TypeVar("TType", bound="PoolEncryptionAlgorithm")

# FIXME: Add PoolTopology
# FIXME: Add PoolDeduplication

@unique
class PoolEncryptionAlgorithm(Enum):
    AES_128_CCM = "AES-128-CCM"
    AES_192_CCM = "AES-192-CCM"
    AES_256_CCM = "AES-256-CCM"
    AES_128_CGM = "AES-128-CGM"
    AES_192_CGM = "AES-192-CGM"
    AES_256_CGM = "AES-256-CGM"

    @classmethod
    def fromValue(cls, value: str) -> TType:
        if value == cls.AES_128_CCM.value:
            return cls.AES_128_CCM
        if value == cls.AES_192_CCM.value:
            return cls.AES_192_CCM
        if value == cls.AES_256_CCM.value:
            return cls.AES_256_CCM
        if value == cls.AES_128_CGM.value:
            return cls.AES_128_CGM
        if value == cls.AES_192_CGM.value:
            return cls.AES_192_CGM
        if value == cls.AES_256_CGM.value:
            return cls.AES_256_CGM
        raise Exception(f"Unexpected pool encryption algorithm '{value}'")



class Pool(object):
    def __init__(self, machine: TMachine, name: str) -> None:
        self._machine = machine
        self._name = name
        self._cached_state = self._state

    @property
    def available(self) -> bool:
        """If the pool exists on the server."""
        return self._name in self._machine._state["pools"]

    '''
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
        if self.available:
            self._cached_state = self._state
            return self._state["serial"]
        return self._cached_state["serial"]

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
        return self._machine._state["disks"][self._name]
    '''
