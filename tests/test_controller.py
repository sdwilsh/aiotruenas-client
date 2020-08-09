import unittest
import websockets

from unittest import IsolatedAsyncioTestCase
from pyfreenas import Controller
from tests.fakes.fakeserver import FreeNASServer
from typing import (
    Any,
    Dict,
    List,
    Union,
)


class TestControllerAuth(IsolatedAsyncioTestCase):
    _server: FreeNASServer

    def setUp(self):
        self._server = FreeNASServer()

    async def asyncTearDown(self):
        await self._server.stop()

    async def test_successful_auth(self):
        controller = await Controller.create(
            self._server.host,
            username=self._server.username,
            password=self._server.password,
        )
        await controller.close()

    async def test_unsuccessful_auth(self):
        with self.assertRaises(websockets.exceptions.SecurityError):
            await Controller.create(
                self._server.host,
                username="not a real user",
                password=self._server.password,
            )


class TestControllerRefresh(IsolatedAsyncioTestCase):
    _server: FreeNASServer
    _controller: Controller

    def setUp(self):
        self._server = FreeNASServer()
        self._server.register_method_handler(
            "disk.query", self._default_disk_query_result,
        )
        self._server.register_method_handler(
            "disk.temperatures", self._default_disk_temperatures_result,
        )
        self._server.register_method_handler(
            "vm.query", self._default_vm_query_result,
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

    def _default_disk_query_result(
        self, *args, **kwargs
    ) -> List[Dict[str, Union[str, int]]]:
        return [
            {
                "description": "Some Desc",
                "model": "Samsung SSD 860 EVO 250GB",
                "name": "ada0",
                "serial": "NOTREALSERIAL",
                "size": 250059350016,
                "type": "SSD",
            },
            {
                "description": "",
                "model": "ATA WDC WD60EFAX-68S",
                "name": "da0",
                "serial": "WD-NOTAREALSERIAL",
                "size": 6001175126016,
                "type": "HDD",
            },
        ]

    def _default_disk_temperatures_result(self, *args, **kwargs) -> Dict[str, int]:
        return {
            "ada0": 34,
            "da0": 29,
        }

    def _default_vm_query_result(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return [
            {
                "description": "Some Desc",
                "id": 1,
                "name": "vm01",
                "status": {"pid": 42, "state": "RUNNING"},
            },
            {
                "description": "",
                "id": 3,
                "name": "vm02",
                "status": {"pid": None, "state": "STOPPED"},
            },
        ]

    async def test_refresh(self):
        await self._controller.refresh()
        self.assertEqual(
            len(self._default_disk_query_result()), len(self._controller.disks),
        )
        for disk in self._controller.disks:
            self.assertEqual(
                self._default_disk_temperatures_result()[disk.name], disk.temperature,
            )
        self.assertEqual(
            len(self._default_vm_query_result()), len(self._controller.vms),
        )


if __name__ == "__main__":
    unittest.main()
