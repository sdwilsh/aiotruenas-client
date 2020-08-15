import ssl
import websockets

from .disk import Disk
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
    _state: Dict[str, Any] = {}
    _disks: List[Disk] = []
    _vms: List[VirturalMachine] = []
    _info: Dict[str, Any] = {}

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
            "vms": {},
        }
        self._disks = []
        self._vms = []
        self._info = {}

    async def refresh(self) -> None:
        self._state = {
            "disks": await self._fetch_disks(),
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
        disks = {disk["name"]: disk for disk in disks}
        if len(disks) > 0:
            temps = await self._client.invoke_method(
                "disk.temperatures", [[disk for disk in disks],],
            )
            for name, temp in temps.items():
                disks[name]["temperature"] = temp

        return disks

    async def _fetch_vms(self) -> Dict[str, dict]:
        assert self._client is not None
        vms = await self._client.invoke_method(
            "vm.query", [[], {"select": ["id", "name", "description", "status",],},],
        )
        return {vm["id"]: vm for vm in vms}

    def _update_properties_from_state(self) -> None:
        # Disks
        available_disks_by_name = {
            disk.name: disk for disk in self._disks if disk.available
        }
        current_disk_names = {disk_name for disk_name in self._state["disks"]}
        disk_names_to_add = current_disk_names - set(available_disks_by_name)
        self._disks = [*available_disks_by_name.values()] + [
            Disk(machine=self, name=disk_name) for disk_name in disk_names_to_add
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
    def vms(self) -> List[VirturalMachine]:
        """Returns a list of virtual machines on the host."""
        return self._vms
