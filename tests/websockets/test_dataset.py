import unittest
from unittest import IsolatedAsyncioTestCase

from aiotruenas_client.dataset import DatasetPropertySource, DatasetType
from aiotruenas_client.websockets import CachingMachine
from aiotruenas_client.websockets.dataset import CachingDataset
from tests.fakes.fakeserver import TrueNASServer


class TestPool(IsolatedAsyncioTestCase):
    _server: TrueNASServer
    _machine: CachingMachine

    def setUp(self):
        self._server = TrueNASServer()

    async def asyncSetUp(self):
        self._machine = await CachingMachine.create(
            self._server.host,
            api_key=self._server.api_key,
            secure=False,
        )

    async def asyncTearDown(self):
        await self._machine.close()
        await self._server.stop()

    async def test_dataset_data_interpretation(self) -> None:
        AVAILABLE_BYTES = 841462824960
        COMMENTS = "this is a comment"
        COMPRESSION_RATIO = 1.19
        DATASET_ID = "ssd0"
        POOL_NAME = "ssd0"
        USED_BYTES = 602317275136
        self._server.register_method_handler(
            "pool.dataset.query",
            lambda *args: [
                {
                    "available": {
                        "parsed": AVAILABLE_BYTES,
                        "rawvalue": str(AVAILABLE_BYTES),
                        "source": "NONE",
                        "value": "784G",
                    },
                    "comments": {
                        "parsed": COMMENTS,
                        "rawvalue": COMMENTS,
                        "source": "LOCAL",
                        "value": COMMENTS,
                    },
                    "compressratio": {
                        "parsed": str(COMPRESSION_RATIO),
                        "rawvalue": str(COMPRESSION_RATIO),
                        "source": "NONE",
                        "value": f"{COMPRESSION_RATIO}x",
                    },
                    "id": DATASET_ID,
                    "pool": POOL_NAME,
                    "type": "FILESYSTEM",
                    "used": {
                        "parsed": USED_BYTES,
                        "rawvalue": str(USED_BYTES),
                        "source": "NONE",
                        "value": "266G",
                    },
                },
            ],
        )

        await self._machine.get_datasets()

        self.assertEqual(len(self._machine.datasets), 1)
        dataset = self._machine.datasets[0]
        self.assertEqual(dataset.available_bytes, AVAILABLE_BYTES)
        assert dataset.comments
        self.assertEqual(dataset.comments.parsedValue, COMMENTS)
        self.assertEqual(dataset.comments.rawValue, COMMENTS)
        self.assertEqual(dataset.comments.source, DatasetPropertySource.LOCAL)
        self.assertEqual(dataset.comments.value, COMMENTS)
        self.assertEqual(dataset.compression_ratio, COMPRESSION_RATIO)
        self.assertEqual(dataset.id, DATASET_ID)
        self.assertEqual(dataset.pool_name, POOL_NAME)
        self.assertEqual(dataset.total_bytes, USED_BYTES + AVAILABLE_BYTES)
        self.assertEqual(dataset.type, DatasetType.FILESYSTEM)
        self.assertEqual(dataset.used_bytes, USED_BYTES)

    async def test_dataset_data_interpretation_no_comments(self) -> None:
        AVAILABLE_BYTES = 841462824960
        COMPRESSION_RATIO = 1.19
        DATASET_ID = "ssd0/myvol"
        POOL_NAME = "ssd0"
        USED_BYTES = 602317275136
        self._server.register_method_handler(
            "pool.dataset.query",
            lambda *args: [
                {
                    "available": {
                        "parsed": AVAILABLE_BYTES,
                        "rawvalue": str(AVAILABLE_BYTES),
                        "source": "NONE",
                        "value": "784G",
                    },
                    "compressratio": {
                        "parsed": str(COMPRESSION_RATIO),
                        "rawvalue": str(COMPRESSION_RATIO),
                        "source": "NONE",
                        "value": f"{COMPRESSION_RATIO}x",
                    },
                    "id": DATASET_ID,
                    "pool": POOL_NAME,
                    "type": "VOLUME",
                    "used": {
                        "parsed": USED_BYTES,
                        "rawvalue": str(USED_BYTES),
                        "source": "NONE",
                        "value": "266G",
                    },
                },
            ],
        )

        await self._machine.get_datasets()

        self.assertEqual(len(self._machine.datasets), 1)
        dataset = self._machine.datasets[0]
        self.assertEqual(dataset.available_bytes, AVAILABLE_BYTES)
        self.assertEqual(dataset.comments, None)
        self.assertEqual(dataset.compression_ratio, COMPRESSION_RATIO)
        self.assertEqual(dataset.id, DATASET_ID)
        self.assertEqual(dataset.pool_name, POOL_NAME)
        self.assertEqual(dataset.total_bytes, USED_BYTES + AVAILABLE_BYTES)
        self.assertEqual(dataset.type, DatasetType.VOLUME)
        self.assertEqual(dataset.used_bytes, USED_BYTES)

    async def test_availability(self) -> None:
        self._server.register_method_handler(
            "pool.dataset.query",
            lambda *args: [
                {
                    "available": {
                        "parsed": 841396957184,
                        "rawvalue": "841396957184",
                        "source": "NONE",
                        "value": "784G",
                    },
                    "compressratio": {
                        "parsed": "1.19",
                        "rawvalue": "1.19",
                        "source": "NONE",
                        "value": "1.19x",
                    },
                    "id": "ssd0/iscsi/sdwilsh-desktop",
                    "pool": "ssd0",
                    "type": "VOLUME",
                    "used": {
                        "parsed": 285263630336,
                        "rawvalue": "285263630336",
                        "source": "NONE",
                        "value": "266G",
                    },
                },
            ],
        )

        await self._machine.get_datasets()

        dataset = self._machine.datasets[0]
        self.assertTrue(dataset.available)

        self._server.register_method_handler(
            "pool.dataset.query",
            lambda *args: [],
            override=True,
        )
        await self._machine.get_datasets()
        self.assertFalse(dataset.available)
        self.assertEqual(len(self._machine.datasets), 0)

    async def test_unavailable_caching(self) -> None:
        """Certain properites have caching even if no longer available"""
        AVAILABLE_BYTES = 841462824960
        COMMENTS = "this is a comment"
        COMPRESSION_RATIO = 1.19
        DATASET_ID = "ssd0"
        POOL_NAME = "ssd0"
        USED_BYTES = 602317275136
        self._server.register_method_handler(
            "pool.dataset.query",
            lambda *args: [
                {
                    "available": {
                        "parsed": AVAILABLE_BYTES,
                        "rawvalue": str(AVAILABLE_BYTES),
                        "source": "NONE",
                        "value": "784G",
                    },
                    "comments": {
                        "parsed": COMMENTS,
                        "rawvalue": COMMENTS,
                        "source": "INHERITED",
                        "value": COMMENTS,
                    },
                    "compressratio": {
                        "parsed": str(COMPRESSION_RATIO),
                        "rawvalue": str(COMPRESSION_RATIO),
                        "source": "NONE",
                        "value": f"{COMPRESSION_RATIO}x",
                    },
                    "id": DATASET_ID,
                    "pool": POOL_NAME,
                    "type": "FILESYSTEM",
                    "used": {
                        "parsed": USED_BYTES,
                        "rawvalue": str(USED_BYTES),
                        "source": "NONE",
                        "value": "266G",
                    },
                },
            ],
        )

        await self._machine.get_datasets()
        dataset = self._machine.datasets[0]
        assert dataset is not None
        self._server.register_method_handler(
            "pool.dataset.query",
            lambda *args: [],
            override=True,
        )
        await self._machine.get_datasets()

        self.assertEqual(dataset.available_bytes, AVAILABLE_BYTES)
        assert dataset.comments
        self.assertEqual(dataset.comments.parsedValue, COMMENTS)
        self.assertEqual(dataset.comments.rawValue, COMMENTS)
        self.assertEqual(dataset.comments.source, DatasetPropertySource.INHERITED)
        self.assertEqual(dataset.comments.value, COMMENTS)
        self.assertEqual(dataset.compression_ratio, COMPRESSION_RATIO)
        self.assertEqual(dataset.id, DATASET_ID)
        self.assertEqual(dataset.pool_name, POOL_NAME)
        self.assertEqual(dataset.total_bytes, USED_BYTES + AVAILABLE_BYTES)
        self.assertEqual(dataset.type, DatasetType.FILESYSTEM)
        self.assertEqual(dataset.used_bytes, USED_BYTES)

    async def test_same_instance_after_get_datasets(self) -> None:
        self._server.register_method_handler(
            "pool.dataset.query",
            lambda *args: [
                {
                    "id": "ssd0",
                },
            ],
        )
        await self._machine.get_datasets()
        original_dataset = self._machine.datasets[0]
        await self._machine.get_datasets()
        new_dataset = self._machine.datasets[0]
        self.assertIs(original_dataset, new_dataset)

    def test_eq_impl(self) -> None:
        self._machine._dataset_fetcher._state = {  # type: ignore
            "ssd0": {
                "id": "ssd0",
            }
        }
        a = CachingDataset(self._machine._dataset_fetcher, "ssd0")  # type: ignore
        b = CachingDataset(self._machine._dataset_fetcher, "ssd0")  # type: ignore
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
