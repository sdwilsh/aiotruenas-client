import asyncio
import ejson
import functools
import uuid
import websockets

from typing import Any, Callable, List
from websockets.client import WebSocketClientProtocol


class FreeNASWebSocketClientProtocol(WebSocketClientProtocol):
    def __init__(self, *args, username: str, password: str, **kwargs):
        super().__init__(*args, **kwargs)
        self._username = username
        self._password = password
        self._method_lock = asyncio.Lock()

    async def handshake(self, *args, **kwargs):
        await WebSocketClientProtocol.handshake(self, *args, **kwargs)
        await self.send(
            ejson.dumps({"msg": "connect", "version": "1", "support": ["1"],})
        )
        recv = ejson.loads(await self.recv())
        if recv["msg"] != "connected":
            await self.close()
            raise websockets.exceptions.NegotiationError("Unable to connect.")

        result = await self.invoke_method(
            "auth.login", [self._username, self._password]
        )
        if not result:
            await self.close()
            raise websockets.exceptions.SecurityError("Unable to authenticate.")

    async def invoke_method(self, method: str, params: List[Any] = []) -> Any:
        async with self._method_lock:
            id = str(uuid.uuid4())
            await super().send(
                ejson.dumps(
                    {"id": id, "msg": "method", "method": method, "params": params,}
                )
            )
            recv = ejson.loads(await super().recv())
            if recv["id"] != id or recv["msg"] != "result":
                raise websockets.exceptions.ProtocolError("Unexpected message")
            return recv["result"]


def freenas_auth_protocol_factory(
    username: str, password: str
) -> Callable[[Any], FreeNASWebSocketClientProtocol]:
    return functools.partial(
        FreeNASWebSocketClientProtocol, username=username, password=password
    )
