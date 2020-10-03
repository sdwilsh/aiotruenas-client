import asyncio
import ejson
import functools
import logging
import pprint
import uuid
import websockets

from typing import (
    Any,
    Callable,
    Dict,
    List,
)
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class TrueNASWebSocketClientProtocol(WebSocketClientProtocol):
    # Keyed by the id of the invoke message.
    _invoke_method_futures: Dict[str, asyncio.Future] = {}

    def __init__(self, *args, username: str, password: str, **kwargs):
        super().__init__(*args, **kwargs)
        self._username = username
        self._password = password

    async def handshake(self, *args, **kwargs):
        await WebSocketClientProtocol.handshake(self, *args, **kwargs)
        await self.send(
            ejson.dumps({"msg": "connect", "version": "1", "support": ["1"],})
        )
        recv = ejson.loads(await self.recv())
        if recv["msg"] != "connected":
            await self.close()
            raise websockets.exceptions.NegotiationError("Unable to connect.")

        asyncio.create_task(self._websocket_message_handler())

        result = await self.invoke_method(
            "auth.login", [self._username, self._password]
        )
        if not result:
            await self.close()
            raise websockets.exceptions.SecurityError("Unable to authenticate.")

    async def invoke_method(self, method: str, params: List[Any] = []) -> Any:
        id = str(uuid.uuid4())
        recv_future = asyncio.get_event_loop().create_future()
        self._invoke_method_futures[id] = recv_future
        await super().send(
            ejson.dumps(
                {"id": id, "msg": "method", "method": method, "params": params,}
            )
        )
        recv = await recv_future
        return recv["result"]

    def _invoke_method_handler(self, message: Dict[str, Any]) -> None:
        if message["id"] not in self._invoke_method_futures:
            logger.error(f"Message id %s is not one we are expecting!", message["id"])
            return
        future = self._invoke_method_futures.pop(message["id"])
        future.set_result(message)

    async def _websocket_message_handler(self) -> None:
        async for message in self:
            recv = ejson.loads(message)
            if recv["msg"] == "result":
                self._invoke_method_handler(recv)
            else:
                logger.error(
                    f"Unhandled message from server:\n%s", pprint.pformat(recv)
                )


def truenas_auth_protocol_factory(
    username: str, password: str
) -> Callable[[Any], TrueNASWebSocketClientProtocol]:
    return functools.partial(
        TrueNASWebSocketClientProtocol, username=username, password=password
    )
