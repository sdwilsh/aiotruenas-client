import ssl
from typing import Any, Dict, List, Optional, TypeVar

import websockets

from ..machine import Machine
from .disk import CachingDisk, CachingDiskStateFetcher
from .pool import CachingPool, CachingPoolStateFetcher
from .protocol import (
    TrueNASWebSocketClientProtocol,
    truenas_api_key_auth_protocol_factory,
    truenas_password_auth_protocol_factory,
)
from .virtualmachine import CachingVirtualMachine, CachingVirtualMachineStateFetcher

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
        api_key: Optional[str] = None,
        password: Optional[str] = None,
        username: Optional[str] = None,
        secure: bool = True,
    ) -> TCachingMachine:
        m = CachingMachine()
        await m.connect(
            host=host,
            api_key=api_key,
            password=password,
            username=username,
            secure=secure,
        )
        return m

    async def connect(
        self,
        host: str,
        api_key: Optional[str],
        password: Optional[str],
        username: Optional[str],
        secure: bool,
    ) -> None:
        """Connects to the remote machine."""
        if api_key and (password or username):
            raise ValueError("Only one of password/username and api_key can be used.")
        if password and not username:
            raise ValueError("Username is missing.")
        if not password and username:
            raise ValueError("Password is missing.")
        if not password and not username and not api_key:
            raise ValueError("Either password/username or api_key must be given.")

        if api_key:
            auth_protocol = truenas_api_key_auth_protocol_factory(api_key)
        if password:
            auth_protocol = truenas_password_auth_protocol_factory(username, password)

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
