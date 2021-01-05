from typing import Any, Dict, List, TypeVar

from ..jail import Jail, JailStatus
from .interfaces import StateFetcher, WebsocketMachine

TCachingJailStateFetcher = TypeVar(
    "TCachingJailStateFetcher", bound="CachingJailStateFetcher"
)


class CachingJail(Jail):
    def __init__(self, fetcher: TCachingJailStateFetcher, name: str) -> None:
        super().__init__(name=name)
        self._fetcher = fetcher
        self._cached_state = self._state

    async def start(self) -> None:
        """Starts a stopped jail."""
        return await self._fetcher._start_jail(self)

    async def stop(self, force: bool = False) -> None:
        """Stops a running jail."""
        return await self._fetcher._stop_jail(self, force)

    async def restart(self) -> None:
        """Restarts a running jail."""
        return await self._fetcher._restart_jail(self)

    @property
    def available(self) -> bool:
        """If the jail exists on the server."""
        return self._name in self._fetcher._state

    @property
    def status(self) -> JailStatus:
        """The status of the jail."""
        assert self.available
        return JailStatus.fromValue(self._state["state"])

    @property
    def _state(self) -> Dict[str, Any]:
        """The state of the jail, according to the Machine."""
        return self._fetcher._get_cached_state(self)


class CachingJailStateFetcher(StateFetcher):
    _parent: WebsocketMachine
    _state: Dict[str, Dict[str, Any]]
    _cached_jails: List[CachingJail]

    def __init__(self, machine: WebsocketMachine) -> None:
        self._parent = machine
        self._state = {}
        self._cached_jails = []

    @classmethod
    async def create(
        cls,
        machine: WebsocketMachine,
    ) -> TCachingJailStateFetcher:
        cjsf = CachingJailStateFetcher(machine=machine)
        return cjsf

    async def get_jails(self) -> List[CachingJail]:
        """Returns a list of jails on the host."""
        self._state = await self._fetch_jails()
        self._update_properties_from_state()
        return self.jails

    @property
    def jails(self) -> List[CachingJail]:
        """Returns a list of jails on the host."""
        return self._cached_jails

    async def _start_jail(self, jail: Jail) -> None:
        if jail.status != JailStatus.DOWN:
            raise RuntimeError(f"Jail {jail.name} is already running.")

        job_id = await self._parent._invoke_method(
            "jail.start",
            [jail.name],
        )
        # TODO: subscribe to core.get_jobs, and wait for completion/error
        # See https://www.truenas.com/docs/hub/additional-topics/api/websocket_api.html#jobs
        return None

    async def _stop_jail(self, jail: Jail, force: bool = False) -> None:
        if jail.status != JailStatus.UP:
            raise RuntimeError(f"Jail {jail.name} is not running.")

        job_id = await self._parent._invoke_method("jail.stop", [jail.name, force])
        # TODO: subscribe to core.get_jobs, and wait for completion/error
        # See https://www.truenas.com/docs/hub/additional-topics/api/websocket_api.html#jobs
        return None

    async def _restart_jail(self, jail: Jail) -> None:
        if jail.status != JailStatus.UP:
            raise RuntimeError(f"Jail {jail.name} is not running.")

        job_id = await self._parent._invoke_method("jail.restart", [jail.name])
        # TODO: subscribe to core.get_jobs, and wait for completion/error
        # See https://www.truenas.com/docs/hub/additional-topics/api/websocket_api.html#jobs
        return None

    def _get_cached_state(self, jail: Jail) -> Dict[str, Any]:
        return self._state[jail.name]

    async def _fetch_jails(self) -> Dict[str, Dict[str, Any]]:
        jails = await self._parent._invoke_method(
            "jail.query",
            [
                [],
                {
                    "select": [
                        "id",
                        "state",
                    ],
                },
            ],
        )
        return {jail["id"]: jail for jail in jails}

    def _update_properties_from_state(self) -> None:
        available_jails_by_name = {
            jail.name: jail for jail in self._cached_jails if jail.available
        }
        current_jail_names = {jail_name for jail_name in self._state}
        jail_names_to_add = current_jail_names - set(available_jails_by_name)
        self._cached_jails = [*available_jails_by_name.values()] + [
            CachingJail(fetcher=self, name=jail_name) for jail_name in jail_names_to_add
        ]
