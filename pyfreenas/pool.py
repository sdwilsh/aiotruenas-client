from enum import Enum, unique
from typing import TypeVar

TMachine = TypeVar("TMachine", bound="Machine")
TStatus = TypeVar("TType", bound="PoolStatus")
#TType = TypeVar("TType", bound="PoolEncryptionAlgorithm")

@unique
class PoolStatus(Enum):
    ONLINE = "ONLINE"
    # FIXME: What are the other statuses?

    @classmethod
    def fromValue(cls, value: str) -> TStatus:
        if value == cls.ONLINE.value:
            return cls.ONLINE
        raise Exception(f"Unexpected pool encryption algorithm '{value}'")

'''
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
'''


class Pool(object):
    def __init__(self, machine: TMachine, id: int) -> None:
        self._machine = machine
        self._id = id
        self._cached_state = self._state

    @property
    def available(self) -> bool:
        """If the pool exists on the Machine."""
        return self._id in self._machine._state["pools"]

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
        if self.available:
            self._cached_state = self._state
            return self._state["guid"]
        return self._cached_state["guid"]

    @property
    def id(self) -> int:
        """The id of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["id"]
        return self._cached_state["id"]

    @property
    def is_decrypted(self) -> bool:
        """Is the pool decrypted."""
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
    def scan(self) -> dict:
        """The scan? of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["scan"]
        return self._cached_state["scan"]

    @property
    def status(self) -> TStatus:
        """The status of the pool."""
        assert self.available:
        return PoolStatus.fromValue(self._state["status"])

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
        return self._machine._state["pools"][self._id]
    '''
