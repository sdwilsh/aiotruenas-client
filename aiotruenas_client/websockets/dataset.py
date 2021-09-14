from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..dataset import Dataset, DatasetProperty, DatasetType
from .interfaces import WebsocketMachine


class CachingDataset(Dataset):
    def __init__(self, fetcher: CachingDatasetStateFetcher, id: str) -> None:
        super().__init__(id)
        self._fetcher = fetcher
        self._cached_state = self._state

    @property
    def available(self) -> bool:
        """If the pool exists on the Machine."""
        return self.id in self._fetcher._state  # type: ignore

    @property
    def available_bytes(self) -> int:
        """The number of available bytes in the dataset."""
        property = self._get_property("available")
        assert property is not None
        return int(property.parsedValue)

    @property
    def comments(self) -> Optional[DatasetProperty]:
        """The user-provided comments on the dataset."""
        property = self._get_property("comments")
        assert property is not None
        return property.parsedValue

    @property
    def compression_ratio(self) -> float:
        """The compression ratio of the dataset."""
        property = self._get_property("compressratio")
        assert property is not None
        return float(property.parsedValue)

    @property
    def pool_name(self) -> str:
        """The name of the dataset's pool."""
        if self.available:
            self._cached_state = self._state
            return self._state["pool"]
        return self._cached_state["pool"]

    @property
    def type(self) -> DatasetType:
        """The type of the dataset."""
        if self.available:
            self._cached_state = self._state
            return DatasetType.fromValue(self._state["type"])
        return DatasetType.fromValue(self._cached_state["type"])

    @property
    def used_bytes(self) -> int:
        """The number of used bytes in the dataset."""
        property = self._get_property("used")
        assert property is not None
        return int(property.parsedValue)

    @property
    def _state(self) -> Dict[str, Any]:
        """The state of the dataset, according to the Machine."""
        return self._fetcher.get_cached_state(self)

    def _get_property(self, property_name: str) -> Optional[DatasetProperty]:
        if self.available:
            self._cached_state = self._state
            if property_name not in self._state:
                return None
            return DatasetProperty(self._state[property_name])

        if property_name not in self._cached_state:
            return None
        return DatasetProperty(self._cached_state[property_name])


class CachingDatasetStateFetcher(object):
    def __init__(self, machine: WebsocketMachine) -> None:
        self._parent = machine
        self._state: Dict[str, Dict[str, Any]] = {}
        self._cached_datasets: List[CachingDataset] = []

    @classmethod
    async def create(
        cls,
        machine: WebsocketMachine,
    ) -> CachingDatasetStateFetcher:
        cpsf = CachingDatasetStateFetcher(machine=machine)
        return cpsf

    async def get_datasets(self) -> List[CachingDataset]:
        """Returns a list of datasets known to the host."""
        self._state = await self._fetch_datasets()
        self._update_properties_from_state()
        return self.datasets

    @property
    def datasets(self) -> List[CachingDataset]:
        """Returns a list of datasets known to the host."""
        return self._cached_datasets

    def get_cached_state(self, dataset: Dataset) -> Dict[str, Any]:
        return self._state[dataset.id]

    async def _fetch_datasets(self) -> Dict[str, Dict[str, Any]]:
        datasets = await self._parent.invoke_method(
            "pool.dataset.query",
            [
                [],
                {
                    "select": [
                        "available",
                        "comments",
                        "compressratio",
                        "id",
                        "pool",
                        "type",
                        "used",
                    ],
                },
            ],
        )
        return {dataset["id"]: dataset for dataset in datasets}

    def _update_properties_from_state(self) -> None:
        available_datasets_by_id = {
            dataset.id: dataset
            for dataset in self._cached_datasets
            if dataset.available
        }
        current_dataset_ids = {dataset_id for dataset_id in self._state}
        dataset_ids_to_add = current_dataset_ids - set(available_datasets_by_id)
        self._cached_datasets = [*available_datasets_by_id.values()] + [
            CachingDataset(fetcher=self, id=dataset_id)
            for dataset_id in dataset_ids_to_add
        ]
