from __future__ import annotations

from typing import Any, Dict, List

from ..pool import Pool, PoolStatus
from .interfaces import WebsocketMachine


class CachingPool(Pool):
    def __init__(self, fetcher: CachingPoolStateFetcher, guid: str) -> None:
        super().__init__(guid)
        self._fetcher = fetcher
        self._cached_state = self._state

    @property
    def available(self) -> bool:
        """If the pool exists on the Machine."""
        return self._guid in self._fetcher._state

    @property
    def encrypt(self) -> int:
        """The encrypt? of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["encrypt"]
        return self._cached_state["encrypt"]

    @property
    def id(self) -> int:
        """The id of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["id"]
        return self._cached_state["id"]

    @property
    def is_decrypted(self) -> bool:
        """Is the pool decrypted?"""
        if self.available:
            self._cached_state = self._state
            return self._state["is_decrypted"]
        return self._cached_state["is_decrypted"]

    @property
    def name(self) -> str:
        """The name of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["name"]
        return self._cached_state["name"]

    @property
    def status(self) -> PoolStatus:
        """The status of the pool."""
        if self.available:
            self._cached_state = self._state
            return PoolStatus.fromValue(self._state["status"])
        return PoolStatus.fromValue(self._cached_state["status"])

    @property
    def topology(self) -> dict:
        """The topology of the pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["topology"]
        return self._cached_state["topology"]

    @property
    def _state(self) -> Dict[str, Any]:
        """The state of the pool, according to the Machine."""
        return self._fetcher._get_cached_state(self)


class CachingPoolStateFetcher(object):
    _parent: WebsocketMachine
    _state: Dict[str, Dict[str, Any]]
    _cached_pools: List[CachingPool]

    def __init__(self, machine: WebsocketMachine) -> None:
        self._parent = machine
        self._state = {}
        self._cached_pools = []

    @classmethod
    async def create(
        cls,
        machine: WebsocketMachine,
    ) -> CachingPoolStateFetcher:
        cpsf = CachingPoolStateFetcher(machine=machine)
        return cpsf

    async def get_pools(self) -> List[CachingPool]:
        """Returns a list of pools known to the host."""
        self._state = await self._fetch_pools()
        self._update_properties_from_state()
        return self.pools

    @property
    def pools(self) -> List[CachingPool]:
        """Returns a list of pools known to the host."""
        return self._cached_pools

    def _get_cached_state(self, pool: Pool) -> Dict[str, Any]:
        return self._state[pool.guid]

    async def _fetch_pools(self) -> Dict[str, Dict[str, Any]]:
        pools = await self._parent._invoke_method(
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
        available_pools_by_guid = {
            pool.guid: pool for pool in self._cached_pools if pool.available
        }
        current_pool_guids = {pool_guid for pool_guid in self._state}
        pool_guids_to_add = current_pool_guids - set(available_pools_by_guid)
        self._cached_pools = [*available_pools_by_guid.values()] + [
            CachingPool(fetcher=self, guid=pool_guid) for pool_guid in pool_guids_to_add
        ]
