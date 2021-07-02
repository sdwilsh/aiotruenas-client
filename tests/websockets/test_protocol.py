from typing import cast
from unittest.async_case import IsolatedAsyncioTestCase

from aiotruenas_client.websockets.protocol import (
    TrueNASWebSocketClientProtocol,
    truenas_api_key_auth_protocol_factory,
)
from tests.fakes.fakeserver import TrueNASServer
from websockets.legacy.client import connect


class TestProtocolSubscriptions(IsolatedAsyncioTestCase):
    _server: TrueNASServer

    def setUp(self):
        self._server = TrueNASServer()

    async def asyncTearDown(self):
        await self._server.stop()

    async def test_two_clients_subscribe(self):
        auth_protocol = truenas_api_key_auth_protocol_factory(self._server.api_key)
        client1 = cast(
            TrueNASWebSocketClientProtocol,
            await connect(
                f"ws://{self._server.host}/websocket",
                create_protocol=auth_protocol,
            ),
        )
        client2 = cast(
            TrueNASWebSocketClientProtocol,
            await connect(
                f"ws://{self._server.host}/websocket",
                create_protocol=auth_protocol,
            ),
        )

        try:
            await client1.subscribe(name="test")
            await client2.subscribe(name="test")
        finally:
            await client1.close()
            await client2.close()
