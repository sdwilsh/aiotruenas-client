import ssl
import websockets

from .pool import Pool
from .websockets.protocol import (
    FreeNASWebSocketClientProtocol,
    freenas_auth_protocol_factory,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
    TypeVar,
)

T = TypeVar("T", bound="Machine")


class Machine(object):
    _client: Optional[FreeNASWebSocketClientProtocol] = None
    _info: Dict[str, Any] = {}
    _state: Dict[str, Any] = {}

    @classmethod
    async def create(
        cls, host: str, password: str, username: str = "root", secure: bool = True
    ) -> T:
        m = Machine()
        await m.connect(host=host, password=password, username=username, secure=secure)
        return m

    async def connect(
        self, host: str, password: str, username: str, secure: bool
    ) -> None:
        """Connects to the remote machine."""
        assert self._client is None
        if not secure:
            protocol = "ws"
            context = None
        else:
            protocol = "wss"
            context = ssl.SSLContext()
        self._client = await websockets.connect(
            f"{protocol}://{host}/websocket",
            create_protocol=freenas_auth_protocol_factory(username, password),
            ssl=context,
        )
        self._info = await self._client.invoke_method("system.info")

    async def close(self) -> None:
        """Closes the conenction to the server."""
        assert self._client is not None
        await self._client.close()
        self._client = None
        self._state = {}
        self._disks = []
        self._info = {}
        self._pools = []
        self._vms = []

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

