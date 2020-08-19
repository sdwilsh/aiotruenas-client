import unittest
import websockets

from unittest import IsolatedAsyncioTestCase
from pyfreenas.websockets import CachingMachine
from tests.fakes.fakeserver import (
    CommonQueries,
    FreeNASServer,
)


class TestCachingMachineAuth(IsolatedAsyncioTestCase):
    _server: FreeNASServer

    def setUp(self):
        self._server = FreeNASServer()

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


if __name__ == "__main__":
    unittest.main()
