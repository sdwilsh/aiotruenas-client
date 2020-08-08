import asyncio
import datetime
import ejson
import random
import string
import uuid
import websockets

from typing import Any, Callable, Dict, List, TypeVar

TServer = TypeVar('TServer', bound='FreeNASServer')
TMethodHandler = Callable[[List[Any]], Any]

DEFAULT_SYSTEM_INFO = {
    "boottime": datetime.datetime(2020, 4, 30, 16, 44, 16, tzinfo=datetime.timezone.utc),
    "buildtime": [datetime.datetime(2020, 4, 21, 16, 43, 21, tzinfo=datetime.timezone.utc)],
    "cores": 12,
    "datetime": datetime.datetime(2020, 8, 8, 22, 8, 2, 489000, tzinfo=datetime.timezone.utc),
    "hostname": "localhost",
    "license": None,
    "loadavg": [0.189453125, 0.18505859375, 0.16552734375],
    "model": "AMD Ryzen 5 3600 6-Core Processor              ",
    "physmem": 34240249856,
    "system_manufacturer": "To Be Filled By O.E.M.",
    "system_product": "To Be Filled By O.E.M.",
    "system_serial": "To Be Filled By O.E.M.",
    "timezone": "America/Los_Angeles",
    "uptime": "3:08PM  up 99 days, 22:24, 8 users",
    "uptime_seconds": 8634225.58104613,
    "version": "FreeNAS-11.3-U2.1",
}


class FreeNASServer(object):

    _username: str
    _password: str
    _serve_handle: websockets.serve

    _method_handlers: Dict[str, TMethodHandler]

    def __init__(self, system_info: Dict[str, Any] = DEFAULT_SYSTEM_INFO):
        self._username = ''.join(random.choice(
            string.ascii_letters) for i in range(6))
        self._password = ''.join(random.choice(
            string.ascii_letters) for i in range(6))
        self._method_handlers = {}

        self.register_method_handler(
            "auth.login",
            lambda args: args[0] == self.username and args[1] == self.password,
        )
        self.register_method_handler(
            "system.info",
            lambda _args: system_info,
        )

        self._serve_handle = websockets.serve(
            self._handle_messages, "localhost", 8000)
        asyncio.get_event_loop().run_until_complete(self._serve_handle)

    def register_method_handler(self, method_name: str, handler: TMethodHandler, override: bool = False) -> None:
        assert override or method_name not in self._method_handlers
        self._method_handlers[method_name] = handler

    async def stop(self) -> None:
        """Shuts down the fake server."""
        if self._serve_handle is None:
            return
        self._serve_handle.ws_server.close()
        await self._serve_handle.ws_server.wait_closed()
        self._serve_handle = None

    @property
    def username(self) -> str:
        """The username that will successfully authenticiate with the server."""
        return self._username

    @property
    def password(self) -> str:
        """The password that will successfully authenticiate with the server."""
        return self._password

    @property
    def host(self) -> str:
        """The host to use to connect to this server."""
        return f"localhost:8000"

    async def _handle_messages(self, websocket: websockets.protocol.WebSocketCommonProtocol, _path: str):
        async def send(data: object) -> None:
            await websocket.send(ejson.dumps(data))

        async def fail():
            await send({
                "msg": "failed",
                "version": "1",
            })

        data = ejson.loads(await websocket.recv())
        if data["msg"] != "connect":
            return await fail()
        await websocket.send(ejson.dumps({
            "msg": "connected",
            "session": str(uuid.uuid4())
        }))
        async for message in websocket:
            data = ejson.loads(message)
            if data["msg"] == "method":
                assert data["method"] in self._method_handlers
                await send({
                    "id": data["id"],
                    "msg": "result",
                    "result": self._method_handlers[data["method"]](data["params"]),
                })
                continue
            await fail()
