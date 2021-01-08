from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..disk import Disk, DiskType
from .interfaces import StateFetcher, WebsocketMachine


class CachingDisk(Disk):
    def __init__(self, fetcher: CachingDiskStateFetcher, serial: str) -> None:
        super().__init__(serial=serial)
        self._fetcher = fetcher
        self._cached_state = self._state

    @property
    def available(self) -> bool:
        """If the disk exists on the server."""
        return self._serial in self._fetcher._state

    @property
    def description(self) -> str:
        """The description of the desk."""
        if self.available:
            self._cached_state = self._state
            return self._state["description"]
        return self._cached_state["description"]

    @property
    def model(self) -> str:
        """The model of the disk."""
        if self.available:
            self._cached_state = self._state
            return self._state["model"]
        return self._cached_state["model"]

    @property
    def name(self) -> str:
        """The name of the disk."""
        if self.available:
            self._cached_state = self._state
            return self._state["name"]
        return self._cached_state["name"]

    @property
    def size(self) -> int:
        """The size of the disk."""
        if self.available:
            self._cached_state = self._state
            return self._state["size"]
        return self._cached_state["size"]

    @property
    def temperature(self) -> Optional[int]:
        """The temperature of the disk."""
        assert self.available
        if "temperature" in self._state:
            return self._state["temperature"]
        return None

    @property
    def type(self) -> DiskType:
        """The type of the desk."""
        if self.available:
            self._cached_state = self._state
            return DiskType.fromValue(self._state["type"])
        return DiskType.fromValue(self._cached_state["type"])

    @property
    def _state(self) -> Dict[str, Any]:
        """The state of the desk, according to the caching fetcher."""
        return self._fetcher._get_cached_state(self)


class CachingDiskStateFetcher(StateFetcher):
    _parent: WebsocketMachine
    _state: Dict[str, Dict[str, Any]]
    _cached_disks: List[CachingDisk]
    _fetch_temperature: bool

    def __init__(self, machine: WebsocketMachine) -> None:
        self._parent = machine
        self._state = {}
        self._cached_disks = []

    @classmethod
    async def create(
        cls,
        machine: WebsocketMachine,
    ) -> CachingDiskStateFetcher:
        cdsf = CachingDiskStateFetcher(machine=machine)
        return cdsf

    async def get_disks(self, include_temperature: bool = False) -> List[CachingDisk]:
        """Returns a list of disks attached to the host."""
        self._fetch_temperature = include_temperature
        self._state = await self._fetch_disks()
        self._update_properties_from_state()
        return self.disks

    @property
    def disks(self) -> List[CachingDisk]:
        """Returns a list of disks attached to the host."""
        return self._cached_disks

    def _get_cached_state(self, disk: Disk) -> Dict[str, Any]:
        return self._state[disk.serial]

    async def _fetch_disks(self) -> Dict[str, Dict[str, Any]]:
        disks = await self._parent._invoke_method(
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
        if len(disks_by_name) > 0 and self._fetch_temperature:
            temps = await self._parent._invoke_method(
                "disk.temperatures",
                [
                    [disk for disk in disks_by_name],
                ],
            )
            for name, temp in temps.items():
                disks_by_name[name]["temperature"] = temp

        # Disks should be keyed by serial for long-term storage (unique), but
        # it is easier to work by name above.
        return {disk["serial"].strip(): disk for disk in disks_by_name.values()}

    def _update_properties_from_state(self) -> None:
        available_disks_by_serial = {
            disk.name: disk for disk in self._cached_disks if disk.available
        }
        current_disk_serials = {disk_serial for disk_serial in self._state}
        disk_serials_to_add = current_disk_serials - set(available_disks_by_serial)
        self._cached_disks = [*available_disks_by_serial.values()] + [
            CachingDisk(fetcher=self, serial=disk_serial)
            for disk_serial in disk_serials_to_add
        ]
