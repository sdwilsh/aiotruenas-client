import ssl
import websockets

from .disk import Disk
from .pool import Pool
from .virtualmachine import VirturalMachine
from .websockets_custom import (
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
    _disks: List[Disk] = []
    _info: Dict[str, Any] = {}
    _state: Dict[str, Any] = {}
    _pools: List[Pool] = []
    _vms: List[VirturalMachine] = []

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
            "disks": {},
            "pools": {},
            "vms": {},
        }
        self._disks = []
        self._info = {}
        self._pools = []
        self._vms = []

    async def refresh(self) -> None:
        self._state = {
            "disks": await self._fetch_disks(),
            "pools": await self._fetch_pools(),
            "vms": await self._fetch_vms(),
        }
        self._update_properties_from_state()

    async def _fetch_disks(self) -> Dict[str, dict]:
        assert self._client is not None
        disks = await self._client.invoke_method(
            "disk.query",
            [
                [],
                {
                    "select": [
                        "description",
                        "model",
                        "name",
                        "serial",
                        "size",
                        "type",
                    ],
                },
            ],
        )
        disks_by_name = {disk["name"]: disk for disk in disks}
        if len(disks_by_name) > 0:
            temps = await self._client.invoke_method(
                "disk.temperatures", [[disk for disk in disks_by_name],],
            )
            for name, temp in temps.items():
                disks_by_name[name]["temperature"] = temp

        # Disks should be keyed by serial for long-term storage (unique), but
        # it is easier to work by name above.
        return {disk["serial"]: disk for disk in disks_by_name.values()}

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

    async def _fetch_vms(self) -> Dict[str, dict]:
        assert self._client is not None
        vms = await self._client.invoke_method(
            "vm.query", [[], {"select": ["id", "name", "description", "status",],},],
        )
        return {vm["id"]: vm for vm in vms}

    def _update_properties_from_state(self) -> None:
        # Disks
        available_disks_by_serial = {
            disk.name: disk for disk in self._disks if disk.available
        }
        current_disk_serials = {disk_serial for disk_serial in self._state["disks"]}
        disk_serials_to_add = current_disk_serials - set(available_disks_by_serial)
        self._disks = [*available_disks_by_serial.values()] + [
            Disk(machine=self, serial=disk_serial)
            for disk_serial in disk_serials_to_add
        ]

        # Pools
        available_pools_by_guid = {
            pool.guid: pool for pool in self._pools if pool.available
        }
        current_pool_guids = {pool_guid for pool_guid in self._state["pools"]}
        pool_guids_to_add = current_pool_guids - set(available_pools_by_guid)
        self._pools = [*available_pools_by_guid.values()] + [
            Pool(machine=self, guid=pool_guid) for pool_guid in pool_guids_to_add
        ]

        # Virtural Machines
        available_vms_by_id = {vm.id: vm for vm in self._vms if vm.available}
        current_vm_ids = {vm_id for vm_id in self._state["vms"]}
        vm_ids_to_add = current_vm_ids - set(available_vms_by_id)
        self._vms = [*available_vms_by_id.values()] + [
            VirturalMachine(machine=self, id=vm_id) for vm_id in vm_ids_to_add
        ]

    @property
    def disks(self) -> List[Disk]:
        """Returns a list of disks attached to the host."""
        return self._disks

    @property
    def info(self) -> Dict[str, Any]:
        return self._info

    @property
    def pools(self) -> List[Pool]:
        """Returns a list of pools known to the host."""
        return self._pools

    @property
    def vms(self) -> List[VirturalMachine]:
        """Returns a list of virtual machines on the host."""
        return self._vms
