import datetime
import unittest
from typing import Any, Dict, List, Union
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from aiotruenas_client.pool import PoolStatus
from aiotruenas_client.websockets import CachingMachine
from aiotruenas_client.websockets.pool import CachingPool
from tests.fakes.fakeserver import (
    TDiskQueryResult,
    TDiskTemperaturesResult,
    TPoolQueryResult,
    TrueNASServer,
    TVmQueryResult,
)


class TestPool(IsolatedAsyncioTestCase):
    _server: TrueNASServer
    _machine: CachingMachine

    def setUp(self):
        self._server = TrueNASServer()

    async def asyncSetUp(self):
        self._machine = await CachingMachine.create(
            self._server.host,
            username=self._server.username,
            password=self._server.password,
            secure=False,
        )

    async def asyncTearDown(self):
        await self._machine.close()
        await self._server.stop()

    async def test_pool_data_interpretation(self) -> None:
        ENCRYPT = 0
        GUID = "1234ABCD"
        ID = 100
        IS_DECRYPTED = True
        NAME = "testpool"
        self._server.register_method_handler(
            "pool.query",
            lambda *args: [
                {
                    "encrypt": ENCRYPT,
                    "encryptkey": "",
                    "guid": GUID,
                    "id": ID,
                    "is_decrypted": IS_DECRYPTED,
                    "name": NAME,
                    "status": "ONLINE",
                    "state": "FINISHED",
                    "topology": {},
                },
            ],
        )

        await self._machine.get_pools()

        self.assertEqual(len(self._machine.pools), 1)
        pool = self._machine.pools[0]
        self.assertEqual(pool.encrypt, ENCRYPT)
        self.assertEqual(pool.guid, GUID)
        self.assertEqual(pool.id, ID)
        self.assertEqual(pool.is_decrypted, IS_DECRYPTED)
        self.assertEqual(pool.name, NAME)
        self.assertEqual(pool.status, PoolStatus.ONLINE)
        # Need to work on the return type of scan.state
        # self.assertEqual(pool.scan["state"], PoolScanState.FINISHED)

    async def test_availability(self) -> None:
        ENCRYPT = 0
        GUID = "1234ABCD"
        ID = 100
        IS_DECRYPTED = True
        NAME = "testpool"
        self._server.register_method_handler(
            "pool.query",
            lambda *args: [
                {
                    "encrypt": ENCRYPT,
                    "encryptkey": "",
                    "guid": GUID,
                    "id": ID,
                    "is_decrypted": IS_DECRYPTED,
                    "name": NAME,
                    "status": "ONLINE",
                    "topology": {},
                },
            ],
        )

        await self._machine.get_pools()

        pool = self._machine.pools[0]
        self.assertTrue(pool.available)

        self._server.register_method_handler(
            "pool.query",
            lambda *args: [],
            override=True,
        )
        await self._machine.get_pools()
        self.assertFalse(pool.available)
        self.assertEqual(len(self._machine.pools), 0)

    async def test_unavailable_caching(self) -> None:
        """Certain properites have caching even if no longer available"""
        ENCRYPT = 0
        GUID = "1234ABCD"
        ID = 100
        IS_DECRYPTED = True
        NAME = "testpool"
        self._server.register_method_handler(
            "pool.query",
            lambda *args: [
                {
                    "encrypt": ENCRYPT,
                    "encryptkey": "",
                    "guid": GUID,
                    "id": ID,
                    "is_decrypted": IS_DECRYPTED,
                    "name": NAME,
                    "status": "ONLINE",
                    "topology": {},
                },
            ],
        )
        await self._machine.get_pools()
        pool = self._machine.pools[0]
        assert pool is not None
        self._server.register_method_handler(
            "pool.query",
            lambda *args: [],
            override=True,
        )
        await self._machine.get_pools()

        self.assertEqual(pool.encrypt, ENCRYPT)
        self.assertEqual(pool.guid, GUID)
        self.assertEqual(pool.id, ID)
        self.assertEqual(pool.is_decrypted, IS_DECRYPTED)
        self.assertEqual(pool.name, NAME)
        self.assertEqual(pool.status, PoolStatus.ONLINE)

    async def test_same_instance_after_get_pools(self) -> None:
        self._server.register_method_handler(
            "pool.query",
            lambda *args: [
                {
                    "guid": 500,
                    "name": "test_pool",
                },
            ],
        )
        await self._machine.get_pools()
        original_pool = self._machine.pools[0]
        await self._machine.get_pools()
        new_pool = self._machine.pools[0]
        self.assertIs(original_pool, new_pool)

    def test_eq_impl(self) -> None:
        self._machine._pool_fetcher._state = {
            "200": {
                "guid": 200,
                "name": "test_pool",
            }
        }
        a = CachingPool(self._machine._pool_fetcher, "200")
        b = CachingPool(self._machine._pool_fetcher, "200")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
