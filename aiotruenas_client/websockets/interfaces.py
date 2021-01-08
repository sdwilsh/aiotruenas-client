from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from ..job import Job, TJobId
from ..machine import Machine


class StateFetcher(ABC):
    @classmethod
    @abstractmethod
    async def create(
        cls,
        machine: WebsocketMachine,
    ) -> StateFetcher:
        """Factory method to create the state fetcher and setup any subscriptions."""


class WebsocketMachine(Machine):
    @classmethod
    @abstractmethod
    async def create(
        cls,
        host: str,
        api_key: Optional[str] = None,
        password: Optional[str] = None,
        username: Optional[str] = None,
        secure: bool = True,
    ) -> WebsocketMachine:
        """Factory method to create a Websocket-based Machine class.

        This method will automatically connect to the remote machine.

        Only one of `api_key` or (`password` and `username`) can be provided.
        """

    @abstractmethod
    async def connect(
        self,
        host: str,
        api_key: Optional[str],
        password: Optional[str],
        username: Optional[str],
        secure: bool,
    ) -> None:
        """Initializes the connection to the server.

        Only one of `api_key` or (`password` and `username`) can be provided.
        """

    @abstractmethod
    async def close(self) -> None:
        """Closes the conenction to the server."""

    @property
    @abstractmethod
    def closed(self) -> bool:
        """If the connection to the server is closed or not."""

    @abstractmethod
    async def wait_for_job(self, id: TJobId) -> Job:
        """Wait for the specified Job from the remote machine to complete, and return it."""

    @abstractmethod
    async def _invoke_method(self, method: str, params: List[Any] = []) -> Any:
        """Invokes a method and returns its result.

        This should only be used by internal classes to this library.
        """

    @abstractmethod
    async def _subscribe(self, subscriber: Subscriber, name: str) -> asyncio.Queue:
        """Subscribes to a topic and populates a `Queue` of data from it.

        This should only be used by internal classes to this library.
        """

    @abstractmethod
    async def _unsubscribe(self, subscriber: Subscriber, name: str) -> None:
        """Unsubscribes from a topic.

        This should only be used by internal classes to this library.
        """


class Subscriber(ABC):
    @abstractmethod
    async def unsubscribe(self) -> None:
        """Called when the connection is closing and the class needs to unsubscribe."""
