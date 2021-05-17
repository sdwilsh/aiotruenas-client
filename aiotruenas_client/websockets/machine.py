from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any, Dict, List, Optional, cast

from aiotruenas_client.job import TJobId
from aiotruenas_client.websockets.jail import CachingJail, CachingJailStateFetcher
from aiotruenas_client.websockets.job import CachingJob, CachingJobFetcher
from websockets.client import connect

from .disk import CachingDisk, CachingDiskStateFetcher
from .interfaces import Subscriber, WebsocketMachine
from .pool import CachingPool, CachingPoolStateFetcher
from .protocol import (
    TrueNASWebSocketClientProtocol,
    truenas_api_key_auth_protocol_factory,
    truenas_password_auth_protocol_factory,
)
from .virtualmachine import CachingVirtualMachine, CachingVirtualMachineStateFetcher

logger = logging.getLogger(__name__)


class CachingMachine(WebsocketMachine):
    """A Machine implementation that connects over websockets and keeps fetched information in-sync with the server."""

    _client: Optional[TrueNASWebSocketClientProtocol] = None
    _subscribers: List[Subscriber] = []

    _disk_fetcher: CachingDiskStateFetcher
    _jail_fetcher: CachingJailStateFetcher
    _job_fetcher: CachingJobFetcher
    _pool_fetcher: CachingPoolStateFetcher
    _vm_fetcher: CachingVirtualMachineStateFetcher

    @classmethod
    async def create(
        cls,
        host: str,
        api_key: Optional[str] = None,
        password: Optional[str] = None,
        username: Optional[str] = None,
        secure: bool = True,
    ) -> CachingMachine:
        m = CachingMachine()
        await m.connect(
            host=host,
            api_key=api_key,
            password=password,
            username=username,
            secure=secure,
        )
        m._job_fetcher = await CachingJobFetcher.create(machine=m)

        m._disk_fetcher = await CachingDiskStateFetcher.create(machine=m)
        m._jail_fetcher = await CachingJailStateFetcher.create(machine=m)
        m._pool_fetcher = await CachingPoolStateFetcher.create(machine=m)
        m._vm_fetcher = await CachingVirtualMachineStateFetcher.create(machine=m)
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
        elif username and password:
            auth_protocol = truenas_password_auth_protocol_factory(username, password)
        else:
            raise AssertionError

        await self._connect(auth_protocol, host, secure)

    async def close(self) -> None:
        """Closes the conenction to the server."""
        assert self._client is not None
        for subscriber in self._subscribers:
            try:
                await subscriber.unsubscribe()
            except Exception as exc:
                logger.exception(
                    "Caught exception while closing connection.",
                    exc_info=exc,
                )
        await self._client.close()
        self._client = None

    @property
    def closed(self) -> bool:
        """Indicates if the connection to the server is closed or not."""
        return self._client is None or self._client.closed

    async def get_disks(self, include_temperature: bool = False) -> List[CachingDisk]:
        """Returns a list of disks attached to the host."""
        return await self._disk_fetcher.get_disks(
            include_temperature=include_temperature,
        )

    @property
    def disks(self) -> List[CachingDisk]:
        """Returns a list of cached disks attached to the host."""
        return self._disk_fetcher.disks

    async def get_jails(self) -> List[CachingJail]:
        """Returns a list of jails configured on the host."""
        return await self._jail_fetcher.get_jails()

    @property
    def jails(self) -> List[CachingJail]:
        """Returns a list of cached jails configured on the host."""
        return self._jail_fetcher.jails

    async def get_job(self, id: TJobId) -> CachingJob:
        """Get the specified Job from the remote machine."""
        return await self._job_fetcher.get_job(id=id)

    async def wait_for_job(self, id: TJobId) -> CachingJob:
        """Wait for the specified Job from the remote machine to complete, and return it."""
        return await self._job_fetcher.wait_for_job(id=id)

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

    async def _connect(self, auth_protocol, host, secure):
        """Executes connection."""
        assert self._client is None
        if not secure:
            protocol = "ws"
            context = None
        else:
            protocol = "wss"
            context = ssl.SSLContext()
        self._client = cast(
            TrueNASWebSocketClientProtocol,
            await connect(
                f"{protocol}://{host}/websocket",
                create_protocol=auth_protocol,
                ssl=context,
            ),
        )

    async def _invoke_method(self, method: str, params: List[Any] = []) -> Any:
        """Invokes a method and returns its result.

        This should only be used by internal classes to this library.
        """
        assert not self.closed
        return await self._client.invoke_method(method=method, params=params)

    async def _subscribe(self, subscriber: Subscriber, name: str) -> asyncio.Queue:
        """Subscribes to a topic and populates a `Queue` of data from it.

        This should only be used by internal classes to this library.
        """
        assert not self.closed
        queue = await self._client.subscribe(name=name)
        self._subscribers.append(subscriber)
        return queue

    async def _unsubscribe(self, subscriber: Subscriber, name: str) -> None:
        """Unsubscribes from a topic.

        This should only be used by internal classes to this library.
        """
        assert not self.closed
        await self._client.unsubscribe(name)
        self._subscribers.remove(subscriber)
