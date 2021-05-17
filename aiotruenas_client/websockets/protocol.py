import asyncio
import functools
import logging
import pprint
import uuid
from abc import abstractmethod
from typing import Any, Callable, Dict, List

import ejson

from websockets.client import WebSocketClientProtocol
from websockets.exceptions import NegotiationError, SecurityError

logger = logging.getLogger(__name__)


class PendingSubscriptionData:
    _name: str
    _future: asyncio.Future

    def __init__(self, name: str, future: asyncio.Future) -> None:
        self._name = name
        self._future = future

    @property
    def name(self) -> str:
        return self._name

    @property
    def future(self) -> asyncio.Future:
        return self._future


class SubscriptionData:
    _id: str
    _queue: asyncio.Queue

    def __init__(self, id: str, queue: asyncio.Queue) -> None:
        self._id = id
        self._queue = queue

    @property
    def id(self) -> str:
        return self._id

    @property
    def queue(self) -> asyncio.Queue:
        return self._queue


class TrueNASWebSocketClientProtocol(WebSocketClientProtocol):
    # Keyed by the id of the invoke message.
    _invoke_method_futures: Dict[str, asyncio.Future] = {}
    # Keyed by the id of the subscribing message.
    _pending_subscription_data: Dict[str, PendingSubscriptionData] = {}
    # Keyed be the "name" when subscribing, which is the "collection" when data comes in.
    _subscription_data: Dict[str, SubscriptionData] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def handshake(self, *args, **kwargs):
        await WebSocketClientProtocol.handshake(self, *args, **kwargs)
        await self.send(
            ejson.dumps(
                {
                    "msg": "connect",
                    "version": "1",
                    "support": ["1"],
                }
            )
        )
        recv = ejson.loads(await self.recv())
        if recv["msg"] != "connected":
            await self.close()
            raise NegotiationError("Unable to connect.")

        asyncio.create_task(self._websocket_message_handler())

        result = await self._authenticate()
        if not result:
            await self.close()
            raise SecurityError("Unable to authenticate.")

    async def invoke_method(self, method: str, params: List[Any] = []) -> Any:
        id = str(uuid.uuid4())
        recv_future = asyncio.get_event_loop().create_future()
        self._invoke_method_futures[id] = recv_future
        await super().send(
            ejson.dumps(
                {
                    "id": id,
                    "msg": "method",
                    "method": method,
                    "params": params,
                }
            )
        )
        recv = await recv_future
        return recv["result"]

    async def subscribe(self, name: str) -> asyncio.Queue:
        assert name not in self._subscription_data, f"Already subscribed to {name}!"
        id = str(uuid.uuid4())
        sub_future = asyncio.get_event_loop().create_future()
        self._pending_subscription_data[id] = PendingSubscriptionData(name, sub_future)
        await super().send(
            ejson.dumps(
                {
                    "id": id,
                    "msg": "sub",
                    "name": name,
                }
            )
        )
        return await sub_future

    async def unsubscribe(
        self,
        name: str,
    ) -> None:
        assert name in self._subscription_data, f"Not currently subscribed to {name}!"
        id = self._subscription_data[name].id
        await super().send(
            ejson.dumps(
                {
                    "id": id,
                    "msg": "unsub",
                }
            )
        )
        del self._subscription_data[name]

    @abstractmethod
    async def _authenticate(self) -> Any:
        """
        Authentication method.

        Must call an `auth` websocket method and return result.  For example:
        ```
        return await self.invoke_method("auth.login_with_api_key", [self._api_key])
        ```
        """

    def _invoke_method_handler(self, message: Dict[str, Any]) -> None:
        if message["id"] not in self._invoke_method_futures:
            logger.error(f"Message id %s is not one we are expecting!", message["id"])
            return
        future = self._invoke_method_futures.pop(message["id"])
        future.set_result(message)

    def _subscription_ready_handler(self, message: Dict[str, Any]) -> None:
        for id in message["subs"]:
            if id not in self._pending_subscription_data:
                logger.error(f"Message id %s is not one we are expecting!", id)
                continue
            pending_sub_data = self._pending_subscription_data.pop(id)
            queue = asyncio.Queue()
            self._subscription_data[pending_sub_data.name] = SubscriptionData(id, queue)
            pending_sub_data.future.set_result(queue)

    def _subscription_message_handler(self, message: Dict[str, Any]) -> None:
        if message["collection"] not in self._subscription_data:
            logger.error(
                f"Subscription for %s is not one we are expecting!",
                message["collection"],
            )
            return
        queue = self._subscription_data[message["collection"]].queue
        queue.put_nowait(message)

    async def _websocket_message_handler(self) -> None:
        async for message in self:
            recv = ejson.loads(message)
            if recv["msg"] == "result":
                self._invoke_method_handler(recv)
            elif recv["msg"] == "ready":
                self._subscription_ready_handler(recv)
            elif recv["msg"] == "added" or recv["msg"] == "changed":
                self._subscription_message_handler(recv)
            else:
                logger.error(
                    f"Unhandled message from server:\n%s", pprint.pformat(recv)
                )


class TrueNASWebSocketClientProtocolPassword(TrueNASWebSocketClientProtocol):
    """Password authentication."""

    def __init__(self, *args, username: str, password: str, **kwargs):
        super().__init__(*args, **kwargs)
        self._username = username
        self._password = password

    async def _authenticate(self) -> Any:
        return await self.invoke_method("auth.login", [self._username, self._password])


class TrueNASWebSocketClientProtocolApiKey(TrueNASWebSocketClientProtocol):
    """Token authentication."""

    def __init__(self, *args, api_key: str, **kwargs):
        super().__init__(*args, **kwargs)
        self._api_key = api_key

    async def _authenticate(self) -> Any:
        return await self.invoke_method("auth.login_with_api_key", [self._api_key])


def truenas_password_auth_protocol_factory(
    username: str,
    password: str,
) -> Callable[[Any], TrueNASWebSocketClientProtocolPassword]:
    return functools.partial(
        TrueNASWebSocketClientProtocolPassword, username=username, password=password
    )


def truenas_api_key_auth_protocol_factory(
    api_key: str,
) -> Callable[[Any], TrueNASWebSocketClientProtocolApiKey]:
    return functools.partial(TrueNASWebSocketClientProtocolApiKey, api_key=api_key)
