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
    _pools: List[Pool] = []

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
        self._state = {
            "pools": {},
        }
        self._disks = []
        self._info = {}
        self._pools = []
        self._vms = []

    async def refresh(self) -> None:
        self._state = {
            "pools": await self._fetch_pools(),
        }
        self._update_properties_from_state()

    async def _fetch_pools(self) -> Dict[str, dict]:
        assert self._client is not None
        pools = await self._client.invoke_method(
            "pool.query",
            [
                [],
                {
                    "select": [
                        "encrypt",
                        "encryptkey",
                        "guid",
                        "id",
                        "is_decrypted",
                        "name",
                        "status",
                        "topology",
                    ],
                },
            ],
        )
        return {pool["guid"]: pool for pool in pools}

    def _update_properties_from_state(self) -> None:
        # Pools
        available_pools_by_guid = {
            pool.guid: pool for pool in self._pools if pool.available
        }
        current_pool_guids = {pool_guid for pool_guid in self._state["pools"]}
        pool_guids_to_add = current_pool_guids - set(available_pools_by_guid)
        self._pools = [*available_pools_by_guid.values()] + [
            Pool(machine=self, guid=pool_guid) for pool_guid in pool_guids_to_add
        ]

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    @property
    def pools(self) -> List[Pool]:
        """Returns a list of pools known to the host."""
        return self._pools

