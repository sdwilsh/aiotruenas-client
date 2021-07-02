from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import Any, Dict, Optional


@unique
class DatasetPropertySource(Enum):
    DEFAULT = "DEFAULT"
    INHERITED = "INHERITED"
    LOCAL = "LOCAL"
    NONE = "NONE"

    @classmethod
    def fromValue(cls, value: str) -> DatasetPropertySource:
        if value == cls.DEFAULT.value:
            return cls.DEFAULT
        if value == cls.INHERITED.value:
            return cls.INHERITED
        if value == cls.LOCAL.value:
            return cls.LOCAL
        if value == cls.NONE.value:
            return cls.NONE
        raise Exception(f"Unexpected dataset property source '{value}'")


class DatasetProperty(object):
    """Represents a Dataset property in TrueNAS"""

    def __init__(self, raw: Dict[str, Any]) -> None:
        self._parsed_value: Any = raw["parsed"]
        self._raw_value: str = raw["rawvalue"]
        self._source: DatasetPropertySource = DatasetPropertySource.fromValue(
            raw["source"]
        )
        self._value: Any = raw["value"]

    @property
    def parsedValue(self) -> Any:
        return self._parsed_value

    @property
    def rawValue(self) -> str:
        return self._raw_value

    @property
    def source(self) -> DatasetPropertySource:
        return self._source

    @property
    def value(self) -> Any:
        return self._value


@unique
class DatasetType(Enum):
    FILESYSTEM = "FILESYSTEM"
    VOLUME = "VOLUME"

    @classmethod
    def fromValue(cls, value: str) -> DatasetType:
        if value == cls.FILESYSTEM.value:
            return cls.FILESYSTEM
        if value == cls.VOLUME.value:
            return cls.VOLUME
        raise Exception(f"Unexpected dataset type '{value}'")


class Dataset(ABC):
    def __init__(self, id: str) -> None:
        self._id = id

    @property
    @abstractmethod
    def available_bytes(self) -> int:
        """The number of available bytes in the dataset."""

    @property
    @abstractmethod
    def comments(self) -> Optional[DatasetProperty]:
        """The user-provided comments on the dataset."""

    @property
    @abstractmethod
    def compression_ratio(self) -> float:
        """The compression ratio of the dataset."""

    @property
    def id(self) -> str:
        """The id of the dataset."""
        return self._id

    @property
    @abstractmethod
    def pool_name(self) -> str:
        """The name of the dataset's pool."""

    @property
    def total_bytes(self) -> int:
        """The number of bytes storable in the dataset."""
        return self.available_bytes + self.used_bytes

    @property
    @abstractmethod
    def type(self) -> DatasetType:
        """The type of the dataset."""

    @property
    @abstractmethod
    def used_bytes(self) -> int:
        """The number of used bytes in the dataset."""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.id.__eq__(other.id)

    def __hash__(self):
        return self.id.__hash__()
