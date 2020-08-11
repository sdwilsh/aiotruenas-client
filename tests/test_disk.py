import unittest

from unittest import IsolatedAsyncioTestCase
from pyfreenas import Controller
from pyfreenas.disk import Disk, DiskType
from tests.fakes.fakeserver import (
    FreeNASServer,
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
    _server: FreeNASServer
    _controller: Controller

    def setUp(self):
        self._server = FreeNASServer()
        self._server.register_method_handler(
            "vm.query", lambda *args: [],
        )

    async def asyncSetUp(self):
        self._controller = await Controller.create(
            self._server.host,
            username=self._server.username,
            password=self._server.password,
        )

    async def asyncTearDown(self):
        await self._controller.close()
        await self._server.stop()

    async def test_ssd_data_interpretation(self) -> None:
        DESCRIPTION = "Some Desc"
        MODEL = "Samsung SSD 860 EVO 250GB"
        NAME = "ada0"
        SERIAL = "NOTREALSERIAL"
        SIZE = 250059350016
        TEMPERATURE = 22
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
        self._server.register_method_handler(
            "disk.temperatures", lambda *args: {NAME: TEMPERATURE},
        )

        await self._controller.refresh()

        self.assertEqual(len(self._controller.disks), 1)
        disk = self._controller.disks[0]
        self.assertEqual(
            disk.description, DESCRIPTION,
        )
        self.assertEqual(disk.model, MODEL)
        self.assertEqual(disk.name, NAME)
        self.assertEqual(disk.serial, SERIAL)
        self.assertEqual(disk.size, SIZE)
        self.assertEqual(disk.temperature, TEMPERATURE)
        self.assertEqual(disk.type, DiskType.SSD)

    async def test_hddd_data_interpretation(self) -> None:
        DESCRIPTION = "Some Desc"
        MODEL = "ATA WDC WD60EFAX-68S"
        NAME = "da0"
        SERIAL = "NOTREALSERIAL"
        SIZE = 6001175126016
        TEMPERATURE = 24
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
            "disk.temperatures", lambda *args: {NAME: TEMPERATURE},
        )

        await self._controller.refresh()

        self.assertEqual(len(self._controller.disks), 1)
        disk = self._controller.disks[0]
        self.assertEqual(
            disk.description, DESCRIPTION,
        )
        self.assertEqual(disk.model, MODEL)
        self.assertEqual(disk.name, NAME)
        self.assertEqual(disk.serial, SERIAL)
        self.assertEqual(disk.size, SIZE)
        self.assertEqual(disk.temperature, TEMPERATURE)
        self.assertEqual(disk.type, DiskType.HDD)

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
            "disk.temperatures", lambda *args: {"ada0": 42},
        )

        await self._controller.refresh()

        disk = self._controller.disks[0]
        self.assertTrue(disk.available)

        self._server.register_method_handler(
            "disk.query", lambda *args: [], override=True,
        )
        await self._controller.refresh()
        self.assertFalse(disk.available)
        self.assertEqual(len(self._controller._disks), 0)

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
            "disk.temperatures", lambda *args: {NAME: 42},
        )
        await self._controller.refresh()
        disk = self._controller.disks[0]
        assert disk is not None
        self._server.register_method_handler(
            "disk.query", lambda *args: [], override=True,
        )
        await self._controller.refresh()

        self.assertEqual(disk.model, MODEL)
        self.assertEqual(disk.name, NAME)
        self.assertEqual(disk.serial, SERIAL)
        self.assertEqual(disk.size, SIZE)
        with self.assertRaises(AssertionError):
            disk.temperature
        self.assertEqual(disk.type, DiskType.HDD)

    async def test_same_instance_after_refresh(self) -> None:
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
            "disk.temperatures", lambda *args: {"ada0": 42},
        )
        await self._controller.refresh()
        original_disk = self._controller.disks[0]
        await self._controller.refresh()
        new_disk = self._controller.disks[0]
        self.assertIs(original_disk, new_disk)


if __name__ == "__main__":
    unittest.main()
