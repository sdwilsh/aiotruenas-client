import ssl
import websockets
from typing import (
    Any,
    Dict,
    List,
    Optional,
    TypeVar,
)
from ..machine import Machine
from .disk import CachingDiskStateFetcher, CachingDisk
from .protocol import (
    FreeNASWebSocketClientProtocol,
    freenas_auth_protocol_factory,
)

TCachingMachine = TypeVar("TCachingMachine", bound="CachingMachine")


class CachingMachine(Machine):
    """A Machine implementation that connects over websockets and keeps fetched information in-sync with the server."""

    _client: Optional[FreeNASWebSocketClientProtocol] = None
    _disk_fetcher: CachingDiskStateFetcher

    def __init__(self) -> None:
        self._disk_fetcher = CachingDiskStateFetcher(self)
        super().__init__()

    @classmethod
    async def create(
        cls, host: str, password: str, username: str = "root", secure: bool = True
    ) -> TCachingMachine:
        m = CachingMachine()
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

    async def close(self) -> None:
        """Closes the conenction to the server."""
        assert self._client is not None
        await self._client.close()
        self._client = None

    async def get_disks(self) -> List[CachingDisk]:
        """Returns a list of disks attached to the host."""
        return await self._disk_fetcher.get_disks()

    @property
    def disks(self) -> List[CachingDisk]:
        """Returns a list of cached disks attached to the host."""
        return self._disk_fetcher.disks

    async def get_vms(self):
        pass
