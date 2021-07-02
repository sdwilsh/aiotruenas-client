import unittest
from unittest import IsolatedAsyncioTestCase

from aiotruenas_client.websockets import CachingMachine
from tests.fakes.fakeserver import TrueNASServer
from websockets.exceptions import SecurityError


class TestCachingMachineAuth(IsolatedAsyncioTestCase):
    _server: TrueNASServer

    def setUp(self):
        self._server = TrueNASServer()

    async def asyncTearDown(self):
        await self._server.stop()

    async def test_successful_auth_password(self):
        machine = await CachingMachine.create(
            self._server.host,
            username=self._server.username,
            password=self._server.password,
            secure=False,
        )
        await machine.close()

    async def test_unsuccessful_auth_password(self):
        with self.assertRaises(SecurityError):
            await CachingMachine.create(
                self._server.host,
                username="not a real user",
                password=self._server.password,
                secure=False,
            )

    async def test_successful_auth_api_key(self):
        machine = await CachingMachine.create(
            self._server.host,
            api_key=self._server.api_key,
            secure=False,
        )
        await machine.close()

    async def test_unsuccessful_auth_api_key(self):
        with self.assertRaises(SecurityError):
            await CachingMachine.create(
                self._server.host,
                api_key="not a real api_key",
                secure=False,
            )

    async def test_unsuccessful_auth_api_key_and_password(self):
        with self.assertRaises(ValueError):
            await CachingMachine.create(
                self._server.host,
                username=self._server.username,
                password=self._server.password,
                api_key=self._server.api_key,
                secure=False,
            )

    async def test_unsuccessful_auth_no_input(self):
        with self.assertRaises(ValueError):
            await CachingMachine.create(
                self._server.host,
                secure=False,
            )

    async def test_unsuccessful_auth_no_username(self):
        with self.assertRaises(ValueError):
            await CachingMachine.create(
                self._server.host,
                password=self._server.password,
                secure=False,
            )

    async def test_unsuccessful_auth_no_password(self):
        with self.assertRaises(ValueError):
            await CachingMachine.create(
                self._server.host,
                username=self._server.username,
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
            "system.info",
            lambda *args: {
                "hostname": HOSTNAME,
            },
        )

        info = await self._machine.get_system_info()

        self.assertTrue("hostname" in info)
        self.assertEqual(info["hostname"], HOSTNAME)


# TODO: for some undiscovered reason, this test prevents subsequent tests from passing with pytest.
# class TestCachingMachineClosed(IsolatedAsyncioTestCase):
#     def setUp(self):
#         self._server = TrueNASServer()

#     async def test_closed(self) -> None:
#         machine = await CachingMachine.create(
#             self._server.host,
#             api_key=self._server.api_key,
#             secure=False,
#         )

#         self.assertFalse(machine.closed)

#         await self._server.stop()
#         self.assertTrue(machine.closed)


if __name__ == "__main__":
    unittest.main()
