import asyncio
from abc import ABC, abstractmethod
from typing import Any, List, Optional, TypeVar

from ..machine import Machine

TStateFetcher = TypeVar("TStateFetcher", bound="StateFetcher")
TWebsocketMachine = TypeVar("TWebsocketMachine", bound="WebsocketMachine")


class StateFetcher(ABC):
    @classmethod
    @abstractmethod
    async def create(
        cls,
        machine: TWebsocketMachine,
    ) -> TStateFetcher:
        """Factory method to create the state fetcher and setup any subscriptions."""


class WebsocketMachine(Machine):
    @staticmethod
    @abstractmethod
    async def create(
        cls,
        host: str,
        api_key: Optional[str] = None,
        password: Optional[str] = None,
        username: Optional[str] = None,
        secure: bool = True,
    ) -> TWebsocketMachine:
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
    async def _invoke_method(self, method: str, params: List[Any] = []) -> Any:
        """Invokes a method and returns its result.

        This should only be used by internal classes to this library.
        """
