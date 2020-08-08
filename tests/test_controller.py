import asyncio
import unittest
import websockets

from unittest import IsolatedAsyncioTestCase
from pyfreenas import Controller
from tests.fakes.fakeserver import FreeNASServer
from typing import Optional


class TestController(IsolatedAsyncioTestCase):
    _server: FreeNASServer
    _controller: Optional[Controller] = None

    def setUp(self):
        self._server = FreeNASServer()

    async def asyncTearDown(self):
        if self._controller is not None:
            await self._controller.close()
        await self._server.stop()

    async def test_successful_auth(self):
        self._controller = await Controller.create(
            self._server.host,
            username=self._server.username,
            password=self._server.password,
        )

    async def test_unsuccessful_auth(self):
        with self.assertRaises(websockets.exceptions.SecurityError):
            await Controller.create(
                self._server.host,
                username="not a real user",
                password=self._server.password,
            )


if __name__ == "__main__":
    unittest.main()
