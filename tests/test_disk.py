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
        SERIAL = "NOTREALSERIAL"
        SIZE = 250059350016
        TEMPERATURE = 22
        self._server.register_method_handler(
            "disk.query",
            lambda *args: [
                {
                    "description": DESCRIPTION,
                    "model": MODEL,
                    "name": "ada0",
                    "serial": SERIAL,
                    "size": SIZE,
                    "type": "SSD",
                },
            ],
        )
        self._server.register_method_handler(
            "disk.temperatures", lambda *args: {"ada0": TEMPERATURE},
        )

        await self._controller.refresh()

        self.assertEqual(len(self._controller.disks), 1)
        disk = self._controller.disks[0]
        self.assertEqual(
            disk.description, DESCRIPTION,
        )
        self.assertEqual(disk.model, MODEL)
        self.assertEqual(disk.serial, SERIAL)
        self.assertEqual(disk.size, SIZE)
        self.assertEqual(disk.temperature, TEMPERATURE)
        self.assertEqual(disk.type, DiskType.SSD)

    async def test_hddd_data_interpretation(self) -> None:
        DESCRIPTION = "Some Desc"
        MODEL = "ATA WDC WD60EFAX-68S"
        SERIAL = "NOTREALSERIAL"
        SIZE = 6001175126016
        TEMPERATURE = 24
        self._server.register_method_handler(
            "disk.query",
            lambda *args: [
                {
                    "description": DESCRIPTION,
                    "model": MODEL,
                    "name": "da0",
                    "serial": SERIAL,
                    "size": SIZE,
                    "type": "HDD",
                },
            ],
        )
        self._server.register_method_handler(
            "disk.temperatures", lambda *args: {"da0": TEMPERATURE},
        )

        await self._controller.refresh()

        self.assertEqual(len(self._controller.disks), 1)
        disk = self._controller.disks[0]
        self.assertEqual(
            disk.description, DESCRIPTION,
        )
        self.assertEqual(disk.model, MODEL)
        self.assertEqual(disk.serial, SERIAL)
        self.assertEqual(disk.size, SIZE)
        self.assertEqual(disk.temperature, TEMPERATURE)
        self.assertEqual(disk.type, DiskType.HDD)


if __name__ == "__main__":
    unittest.main()
