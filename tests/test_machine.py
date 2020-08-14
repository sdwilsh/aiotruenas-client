import unittest
import websockets

from unittest import IsolatedAsyncioTestCase
from pyfreenas import Machine
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


class TestMachineAuth(IsolatedAsyncioTestCase):
    _server: FreeNASServer

    def setUp(self):
        self._server = FreeNASServer()

    async def asyncTearDown(self):
        await self._server.stop()

    async def test_successful_auth(self):
        machine = await Machine.create(
            self._server.host,
            username=self._server.username,
            password=self._server.password,
            secure=False,
        )
        await machine.close()

    async def test_unsuccessful_auth(self):
        with self.assertRaises(websockets.exceptions.SecurityError):
            await Machine.create(
                self._server.host,
                username="not a real user",
                password=self._server.password,
                secure=False,
            )


class TestMachineRefresh(IsolatedAsyncioTestCase):
    _server: FreeNASServer
    _machine: Machine

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
        self._machine = await Machine.create(
            self._server.host,
            username=self._server.username,
            password=self._server.password,
            secure=False,
        )

    async def asyncTearDown(self):
        await self._machine.close()
        await self._server.stop()

    async def test_refresh(self):
        await self._machine.refresh()
        self.assertEqual(
            len(CommonQueries.disk_query_result()), len(self._machine.disks),
        )
        for disk in self._machine.disks:
            self.assertEqual(
                CommonQueries.disk_temperatures_result()[disk.name], disk.temperature,
            )
        self.assertEqual(
            len(CommonQueries.vm_query_result()), len(self._machine.vms),
        )


if __name__ == "__main__":
    unittest.main()
