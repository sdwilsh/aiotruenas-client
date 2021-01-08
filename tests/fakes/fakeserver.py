from __future__ import annotations

import asyncio
import datetime
import random
import string
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

import ejson

import websockets

TMethodHandler = Union[
    Callable[[Any], Any],
    Callable[[Any, Any], Any],
]

TDiskQueryResult = List[Dict[str, Union[str, int]]]
TDiskTemperaturesResult = Dict[str, int]
TPoolQueryResult = List[Dict[str, Any]]
TVmQueryResult = List[Dict[str, Any]]


class TrueNASServer(object):

    _username: str
    _password: str
    _api_key: str
    _serve_handle: Optional[websockets.serve]
    # Mapping of topic to subscription id
    _subscriptions: Dict[str, str] = {}
    _subscription_queue: asyncio.Queue
    _subscription_task: Optional[asyncio.Task] = None

    _method_handlers: Dict[str, TMethodHandler]

    def __init__(self):
        self._username = "".join(random.choice(string.ascii_letters) for i in range(6))
        self._password = "".join(random.choice(string.ascii_letters) for i in range(6))
        self._api_key = "".join(random.choice(string.ascii_letters) for i in range(6))
        self._method_handlers = {}

        self.register_method_handler(
            "auth.login",
            lambda u, p: u == self.username and p == self.password,
        )

        self.register_method_handler(
            "auth.login_with_api_key",
            lambda t: t == self.api_key,
        )

        self._subscription_queue = asyncio.Queue()

        self._serve_handle = websockets.serve(self._handle_messages, "localhost", 8000)
        asyncio.get_event_loop().run_until_complete(self._serve_handle)

    def register_method_handler(
        self, method_name: str, handler: TMethodHandler, override: bool = False
    ) -> None:
        assert override or method_name not in self._method_handlers
        self._method_handlers[method_name] = handler

    async def stop(self) -> None:
        """Shuts down the fake server."""
        if self._serve_handle is None:
            return
        if self._subscription_task:
            self._subscription_task.cancel()
            self._subscription_task = None
        self._serve_handle.ws_server.close()
        await self._serve_handle.ws_server.wait_closed()
        self._serve_handle = None

    def send_subscription_data(self, data: object) -> None:
        """Sends a message to any listenting subscriptions."""
        self._subscription_queue.put_nowait(data)

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
        return "localhost:8000"

    @property
    def api_key(self) -> str:
        """The api_key that will successfully authenticate with the server."""
        return self._api_key

    async def _handle_messages(
        self, websocket: websockets.protocol.WebSocketCommonProtocol, _path: str
    ):
        async def send(data: object) -> None:
            await websocket.send(ejson.dumps(data))

        self._subscription_task = asyncio.create_task(
            self._send_subscription_messages(
                send=send,
            )
        )

        async def fail():
            await send(
                {
                    "msg": "failed",
                    "version": "1",
                }
            )

        data = ejson.loads(await websocket.recv())
        if data["msg"] != "connect":
            return await fail()
        await websocket.send(
            ejson.dumps({"msg": "connected", "session": str(uuid.uuid4())})
        )
        async for message in websocket:
            data = ejson.loads(message)
            if data["msg"] == "method":
                assert data["method"] in self._method_handlers
                await send(
                    {
                        "id": data["id"],
                        "msg": "result",
                        "result": self._method_handlers[data["method"]](
                            *data["params"]
                        ),
                    }
                )
                continue
            if data["msg"] == "sub":
                self._subscriptions[data["name"]] = data["id"]
                await send(
                    {
                        "msg": "ready",
                        "subs": [data["id"]],
                    }
                )
                continue
            if data["msg"] == "unsub":
                topic = [
                    topic
                    for topic, id in self._subscriptions.items()
                    if id == data["id"]
                ][0]
                del self._subscriptions[topic]
                # Nothing to respond with in this case.
                continue

            await fail()

    async def _send_subscription_messages(
        self, send: Callable[[object], Coroutine[None]]
    ) -> None:
        queue = self._subscription_queue
        while True:
            item = await queue.get()
            await send(item)
            queue.task_done()


class CommonQueries:
    @classmethod
    def disk_query_result(cls, *args, **kwargs) -> TDiskQueryResult:
        return [
            {
                "description": "Some Desc",
                "model": "Samsung SSD 860 EVO 250GB",
                "name": "ada0",
                "serial": "NOTREALSERIAL",
                "size": 250059350016,
                "type": "SSD",
            },
            {
                "description": "",
                "model": "ATA WDC WD60EFAX-68S",
                "name": "da0",
                "serial": "WD-NOTAREALSERIAL",
                "size": 6001175126016,
                "type": "HDD",
            },
        ]

    @classmethod
    def disk_temperatures_result(cls, *args, **kwargs) -> TDiskTemperaturesResult:
        return {
            "ada0": 34,
            "da0": 29,
        }

    @classmethod
    def vm_query_result(cls, *args, **kwargs) -> TVmQueryResult:
        return [
            {
                "description": "Some Desc",
                "id": 1,
                "name": "vm01",
                "status": {"pid": 42, "state": "RUNNING"},
            },
            {
                "description": "",
                "id": 3,
                "name": "vm02",
                "status": {"pid": None, "state": "STOPPED"},
            },
        ]

    @classmethod
    def pool_query_result(cls, *args, **kwargs) -> TPoolQueryResult:
        return [
            {
                "encrypt": 0,
                "encryptkey": "",
                "guid": "16006326459371220184",
                "id": 4,
                "is_decrypted": True,
                "name": "testpool",
                "scan": {
                    "bytes_issued": 90546145402880,
                    "bytes_processed": 90902589915136,
                    "bytes_to_process": 90546369048576,
                    "end_time": datetime.datetime(
                        2020, 8, 16, 5, 43, 3, tzinfo=datetime.timezone.utc
                    ),
                    "errors": 0,
                    "function": "SCRUB",
                    "pause": None,
                    "percentage": 99.60788488388062,
                    "start_time": datetime.datetime(
                        2020, 8, 14, 16, 0, 34, tzinfo=datetime.timezone.utc
                    ),
                    "state": "FINISHED",
                },
                "status": "ONLINE",
                "topology": {},
            }
        ]
