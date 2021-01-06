from abc import ABC, abstractmethod
from enum import Enum, unique
from typing import Any, Optional, TypeVar

TJobId = int
TJobStatus = TypeVar("TJobStatus", bound="JobStatus")


@unique
class JobStatus(Enum):
    FAILED = "FAILED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    WAITING = "WAITING"

    @classmethod
    def fromValue(cls, value: str) -> TJobStatus:
        if value == cls.FAILED.value:
            return cls.FAILED
        if value == cls.RUNNING.value:
            return cls.RUNNING
        if value == cls.SUCCESS.value:
            return cls.SUCCESS
        if value == cls.WAITING.value:
            return cls.WAITING
        raise AssertionError(f"Unexpected job state '{value}'")


class Job(ABC):
    def __init__(
        self,
        id: TJobId,
        method: str,
    ) -> None:
        self._id = id
        self._method = method

    @property
    @abstractmethod
    def error(self) -> Optional[str]:
        """The error message from the API."""

    @property
    def id(self) -> TJobId:
        """The job identifying number."""
        return self._id

    @property
    def method(self) -> str:
        """The method that created the job."""
        return self._method

    @property
    @abstractmethod
    def result(self) -> Optional[Any]:
        """The result of the job."""

    @property
    @abstractmethod
    def status(self) -> JobStatus:
        """The status of the job."""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.id.__eq__(other.id)

    def __hash__(self):
        return self.id.__hash__()
