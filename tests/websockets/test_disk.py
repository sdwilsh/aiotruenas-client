import unittest

from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock
from aiotruenas_client.disk import DiskType
from aiotruenas_client.websockets.disk import CachingDisk
from aiotruenas_client.websockets.machine import CachingMachine
from tests.fakes.fakeserver import (
    TrueNASServer,
    TDiskQueryResult,
    TDiskTemperaturesResult,
    TVmQueryResult,
)
from typing import (
    Any,
    Dict,
    List,
    Union,
)


class TestDisk(IsolatedAsyncioTestCase):
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

    async def test_ssd_data_interpretation(self) -> None:
        DESCRIPTION = "Some Desc"
        MODEL = "Samsung SSD 860 EVO 250GB"
        NAME = "ada0"
        SERIAL = "NOTREALSERIAL"
        SIZE = 250059350016
        self._server.register_method_handler(
            "disk.query",
            lambda *args: [
                {
                    "description": DESCRIPTION,
                    "model": MODEL,
                    "name": NAME,
                    "serial": SERIAL,
                    "size": SIZE,
                    "type": "SSD",
                },
            ],
        )

        await self._machine.get_disks()

        self.assertEqual(len(self._machine.disks), 1)
        disk = self._machine.disks[0]
        self.assertEqual(
            disk.description,
            DESCRIPTION,
        )
        self.assertEqual(disk.model, MODEL)
        self.assertEqual(disk.name, NAME)
        self.assertEqual(disk.serial, SERIAL)
        self.assertEqual(disk.size, SIZE)
        self.assertEqual(disk.temperature, None)
        self.assertEqual(disk.type, DiskType.SSD)

    async def test_hddd_data_interpretation(self) -> None:
        DESCRIPTION = "Some Desc"
        MODEL = "ATA WDC WD60EFAX-68S"
        NAME = "da0"
        SERIAL = "NOTREALSERIAL"
        SIZE = 6001175126016
        self._server.register_method_handler(
            "disk.query",
            lambda *args: [
                {
                    "description": DESCRIPTION,
                    "model": MODEL,
                    "name": NAME,
                    "serial": SERIAL,
                    "size": SIZE,
                    "type": "HDD",
                },
            ],
        )

        await self._machine.get_disks()

        self.assertEqual(len(self._machine.disks), 1)
        disk = self._machine.disks[0]
        self.assertEqual(
            disk.description,
            DESCRIPTION,
        )
        self.assertEqual(disk.model, MODEL)
        self.assertEqual(disk.name, NAME)
        self.assertEqual(disk.serial, SERIAL)
        self.assertEqual(disk.size, SIZE)
        self.assertEqual(disk.temperature, None)
        self.assertEqual(disk.type, DiskType.HDD)

    async def test_temperature(self) -> None:
        TEMPERATURE = 42
        self._server.register_method_handler(
            "disk.query",
            lambda *args: [
                {
                    "description": "Some Desc",
                    "model": "Samsung SSD 860 EVO 250GB",
                    "name": "ada0",
                    "serial": "NOTREALSERIAL",
                    "size": 250059350016,
                    "type": "SSD",
                },
            ],
        )
        self._server.register_method_handler(
            "disk.temperatures",
            lambda *args: {"ada0": TEMPERATURE},
        )

        await self._machine.get_disks(include_temperature=True)

        self.assertEqual(len(self._machine.disks), 1)
        disk = self._machine.disks[0]
        self.assertEqual(disk.temperature, TEMPERATURE)

    async def test_availability(self) -> None:
        self._server.register_method_handler(
            "disk.query",
            lambda *args: [
                {
                    "description": "Some Desc",
                    "model": "Samsung SSD 860 EVO 250GB",
                    "name": "ada0",
                    "serial": "NOTREALSERIAL",
                    "size": 250059350016,
                    "type": "SSD",
                },
            ],
        )
        self._server.register_method_handler(
            "disk.temperatures",
            lambda *args: {"ada0": 42},
        )

        await self._machine.get_disks()

        disk = self._machine.disks[0]
        self.assertTrue(disk.available)

        self._server.register_method_handler(
            "disk.query",
            lambda *args: [],
            override=True,
        )
        await self._machine.get_disks()
        self.assertFalse(disk.available)
        self.assertEqual(len(self._machine._disk_fetcher._cached_disks), 0)

    async def test_unavailable_caching(self) -> None:
        """Certain properites have caching even if no longer available"""
        DESCRIPTION = "Some Desc"
        MODEL = "ATA WDC WD60EFAX-68S"
        NAME = "da0"
        SERIAL = "NOTREALSERIAL"
        SIZE = 6001175126016
        self._server.register_method_handler(
            "disk.query",
            lambda *args: [
                {
                    "description": DESCRIPTION,
                    "model": MODEL,
                    "name": NAME,
                    "serial": SERIAL,
                    "size": SIZE,
                    "type": "HDD",
                },
            ],
        )
        self._server.register_method_handler(
            "disk.temperatures",
            lambda *args: {NAME: 42},
        )
        await self._machine.get_disks()
        disk = self._machine.disks[0]
        assert disk is not None
        self._server.register_method_handler(
            "disk.query",
            lambda *args: [],
            override=True,
        )
        await self._machine.get_disks()

        self.assertEqual(disk.model, MODEL)
        self.assertEqual(disk.name, NAME)
        self.assertEqual(disk.serial, SERIAL)
        self.assertEqual(disk.size, SIZE)
        with self.assertRaises(AssertionError):
            disk.temperature
        self.assertEqual(disk.type, DiskType.HDD)

    async def test_same_instance_after_get_disks(self) -> None:
        self._server.register_method_handler(
            "disk.query",
            lambda *args: [
                {
                    "description": "Some Desc",
                    "model": "Samsung SSD 860 EVO 250GB",
                    "name": "ada0",
                    "serial": "NOTREALSERIAL",
                    "size": 250059350016,
                    "type": "SSD",
                },
            ],
        )
        self._server.register_method_handler(
            "disk.temperatures",
            lambda *args: {"ada0": 42},
        )
        await self._machine.get_disks()
        original_disk = self._machine.disks[0]
        await self._machine.get_disks()
        new_disk = self._machine.disks[0]
        self.assertIs(original_disk, new_disk)

    def test_eq_impl(self) -> None:
        self._machine._disk_fetcher._state = {
            "ada0": {
                "description": "",
                "model": "",
                "name": "ada0",
                "serial": "someserial",
                "size": 256,
                "temperature": 42,
                "type": "SSD",
            }
        }
        a = CachingDisk(self._machine._disk_fetcher, "ada0")
        b = CachingDisk(self._machine._disk_fetcher, "ada0")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
