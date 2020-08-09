import unittest
import websockets

from unittest import IsolatedAsyncioTestCase
from pyfreenas import Controller
from tests.fakes.fakeserver import (
    CommonQueries,
    FreeNASServer,
)
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
            "disk.query", CommonQueries.disk_query_result,
        )
        self._server.register_method_handler(
            "disk.temperatures", CommonQueries.disk_temperatures_result,
        )
        self._server.register_method_handler(
            "vm.query", CommonQueries.vm_query_result,
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

    async def test_refresh(self):
        await self._controller.refresh()
        self.assertEqual(
            len(CommonQueries.disk_query_result()), len(self._controller.disks),
        )
        for disk in self._controller.disks:
            self.assertEqual(
                CommonQueries.disk_temperatures_result()[disk.name], disk.temperature,
            )
        self.assertEqual(
            len(CommonQueries.vm_query_result()), len(self._controller.vms),
        )


if __name__ == "__main__":
    unittest.main()
