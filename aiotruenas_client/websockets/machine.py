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
from .pool import CachingPoolStateFetcher, CachingPool
from .virtualmachine import CachingVirtualMachineStateFetcher, CachingVirtualMachine
from .protocol import (
    TrueNASWebSocketClientProtocol,
    truenas_auth_protocol_factory,
)

TCachingMachine = TypeVar("TCachingMachine", bound="CachingMachine")


class CachingMachine(Machine):
    """A Machine implementation that connects over websockets and keeps fetched information in-sync with the server."""

    _client: Optional[TrueNASWebSocketClientProtocol] = None
    _disk_fetcher: CachingDiskStateFetcher
    _pool_fetcher: CachingPoolStateFetcher
    _vm_fetcher: CachingVirtualMachineStateFetcher

    def __init__(self) -> None:
        self._disk_fetcher = CachingDiskStateFetcher(self)
        self._pool_fetcher = CachingPoolStateFetcher(self)
        self._vm_fetcher = CachingVirtualMachineStateFetcher(self)
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
            create_protocol=truenas_auth_protocol_factory(username, password),
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

    async def get_pools(self) -> List[CachingPool]:
        """Returns a list of pools known to the host."""
        return await self._pool_fetcher.get_pools()

    @property
    def pools(self) -> List[CachingPool]:
        """Returns a list of pools known to the host."""
        return self._pool_fetcher.pools

    async def get_vms(self) -> List[CachingVirtualMachine]:
        """Returns a list of virtual machines on the host."""
        return await self._vm_fetcher.get_vms()

    @property
    def vms(self) -> List[CachingVirtualMachine]:
        """Returns a list of cached virtual machines on the host."""
        return self._vm_fetcher.vms
