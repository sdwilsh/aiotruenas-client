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
    truenas_password_auth_protocol_factory,
    truenas_token_auth_protocol_factory,
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
        cls,
        host: str,
        password: Optional[str] = None,
        username: Optional[str] = "root",
        secure: bool = True,
        token: Optional[str] = None,
    ) -> TCachingMachine:
        if password is not None and token is not None:
            raise ValueError("Only one of password and token can be used.")
        if password is None and token is None:
            raise ValueError("Either password or token must be goven.")
        m = CachingMachine()
        await m.connect(
            host=host,
            password=password,
            username=username,
            secure=secure,
            token=token,
        )
        return m

    async def connect(
        self,
        host: str,
        password: Optional[str],
        username: Optional[str],
        secure: bool,
        token: Optional[str],
    ) -> None:
        """Connects to the remote machine."""
        if password is not None:
            auth_protocol = truenas_password_auth_protocol_factory(username, password)
        if token is not None:
            auth_protocol = truenas_token_auth_protocol_factory(token)
        await self._connect(auth_protocol, host, secure)

    async def _connect(self, auth_protocol, host, secure):
        """Executes connection."""
        assert self._client is None
        if not secure:
            protocol = "ws"
            context = None
        else:
            protocol = "wss"
            context = ssl.SSLContext()
        self._client = await websockets.connect(
            f"{protocol}://{host}/websocket",
            create_protocol=auth_protocol,
            ssl=context,
        )

    async def close(self) -> None:
        """Closes the conenction to the server."""
        assert self._client is not None
        await self._client.close()
        self._client = None

    async def get_disks(self, include_temperature: bool = False) -> List[CachingDisk]:
        """Returns a list of disks attached to the host."""
        return await self._disk_fetcher.get_disks(
            include_temperature=include_temperature,
        )

    @property
    def disks(self) -> List[CachingDisk]:
        """Returns a list of cached disks attached to the host."""
        return self._disk_fetcher.disks

    async def get_system_info(self) -> Dict[str, Any]:
        """Get some basic information about the remote machine."""
        assert self._client is not None
        return await self._client.invoke_method("system.info")

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
