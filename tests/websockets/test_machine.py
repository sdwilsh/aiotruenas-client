import unittest
import websockets

from unittest import IsolatedAsyncioTestCase
from aiotruenas_client.websockets import CachingMachine
from tests.fakes.fakeserver import (
    CommonQueries,
    TrueNASServer,
)


class TestCachingMachineAuth(IsolatedAsyncioTestCase):
    _server: TrueNASServer

    def setUp(self):
        self._server = TrueNASServer()

    async def asyncTearDown(self):
        await self._server.stop()

    async def test_successful_auth(self):
        machine = await CachingMachine.create(
            self._server.host,
            username=self._server.username,
            password=self._server.password,
            secure=False,
        )
        await machine.close()

    async def test_unsuccessful_auth(self):
        with self.assertRaises(websockets.exceptions.SecurityError):
            await CachingMachine.create(
                self._server.host,
                username="not a real user",
                password=self._server.password,
                secure=False,
            )


class TestCachingMachineGetSystemInfo(IsolatedAsyncioTestCase):
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

    async def test_get_system_info(self) -> None:
        HOSTNAME = "some.hostname.com"
        self._server.register_method_handler(
            "system.info", lambda *args: {"hostname": HOSTNAME,}
        )

        info = await self._machine.get_system_info()

        self.assertTrue("hostname" in info)
        self.assertEqual(info["hostname"], HOSTNAME)


if __name__ == "__main__":
    unittest.main()
