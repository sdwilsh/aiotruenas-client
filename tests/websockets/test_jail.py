import datetime
import unittest
from unittest import IsolatedAsyncioTestCase

from aiotruenas_client.jail import JailStatus
from aiotruenas_client.websockets import CachingMachine
from aiotruenas_client.websockets.jail import CachingJail
from tests.fakes.fakeserver import TrueNASServer


class TestJail(IsolatedAsyncioTestCase):
    _server: TrueNASServer
    _machine: CachingMachine

    def setUp(self):
        self._server = TrueNASServer()

    async def asyncSetUp(self):
        self._machine = await CachingMachine.create(
            self._server.host,
            api_key=self._server.api_key,
            secure=False,
        )

    async def asyncTearDown(self):
        await self._machine.close()
        await self._server.stop()

    async def test_running_data_interpretation(self) -> None:
        NAME = "jail01"
        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": NAME,
                    "state": "up",
                },
            ],
        )

        await self._machine.get_jails()

        self.assertEqual(len(self._machine.jails), 1)
        jail = self._machine.jails[0]
        self.assertEqual(jail.name, NAME)
        self.assertEqual(jail.status, JailStatus.UP)

    async def test_stopped_data_interpretation(self) -> None:
        NAME = "jail01"
        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": NAME,
                    "state": "down",
                },
            ],
        )

        await self._machine.get_jails()

        self.assertEqual(len(self._machine.jails), 1)
        jail = self._machine.jails[0]
        self.assertEqual(jail.name, NAME)
        self.assertEqual(jail.status, JailStatus.DOWN)

    async def test_availability(self) -> None:
        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": "jail01",
                    "state": "up",
                },
            ],
        )

        await self._machine.get_jails()

        jail = self._machine.jails[0]
        self.assertTrue(jail.available)

        self._server.register_method_handler(
            "jail.query",
            lambda *args: [],
            override=True,
        )
        await self._machine.get_jails()
        self.assertFalse(jail.available)
        self.assertEqual(len(self._machine.jails), 0)

    async def test_same_instance_after_get_jails(self) -> None:
        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": "jail01",
                    "state": "up",
                },
            ],
        )
        await self._machine.get_jails()
        original_jail = self._machine.jails[0]
        await self._machine.get_jails()
        new_jail = self._machine.jails[0]
        self.assertIs(original_jail, new_jail)

    async def test_start(self) -> None:
        NAME = "jail01"
        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": NAME,
                    "state": "up",
                },
            ],
        )
        await self._machine.get_jails()
        jail = self._machine.jails[0]
        with self.assertRaises(RuntimeError):
            await jail.start()

        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": NAME,
                    "state": "down",
                },
            ],
            override=True,
        )

        def start_handler(name) -> int:
            JOB_ID = 42
            self.assertEqual(name, NAME)
            self._server.send_subscription_data(
                {
                    "msg": "changed",
                    "collection": "core.get_jobs",
                    "id": JOB_ID,
                    "fields": {
                        "id": JOB_ID,
                        "method": "jail.start",
                        "arguments": [NAME],
                        "logs_path": None,
                        "logs_excerpt": None,
                        "progress": {
                            "percent": 100,
                            "description": None,
                            "extra": None,
                        },
                        "result": True,
                        "error": None,
                        "exception": None,
                        "exc_info": None,
                        "state": "SUCCESS",
                        "time_started": datetime.datetime(
                            2021, 1, 7, 21, 30, 0, tzinfo=datetime.timezone.utc
                        ),
                        "time_finished": datetime.datetime(
                            2021, 1, 7, 21, 30, 1, tzinfo=datetime.timezone.utc
                        ),
                    },
                },
            ),
            return JOB_ID

        self._server.register_method_handler(
            "jail.start",
            start_handler,
        )
        await self._machine.get_jails()
        jail = self._machine.jails[0]

        self.assertTrue(await jail.start())

    async def test_stop(self) -> None:
        NAME = "jail01"
        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": NAME,
                    "state": "down",
                },
            ],
        )
        await self._machine.get_jails()
        jail = self._machine.jails[0]
        with self.assertRaises(RuntimeError):
            await jail.stop()

        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": NAME,
                    "state": "up",
                },
            ],
            override=True,
        )

        def stop_handler(name, force) -> int:
            JOB_ID = 42
            self.assertEqual(name, NAME)
            self.assertFalse(force)
            self._server.send_subscription_data(
                {
                    "msg": "changed",
                    "collection": "core.get_jobs",
                    "id": JOB_ID,
                    "fields": {
                        "id": JOB_ID,
                        "method": "jail.stop",
                        "arguments": [NAME],
                        "logs_path": None,
                        "logs_excerpt": None,
                        "progress": {
                            "percent": 100,
                            "description": None,
                            "extra": None,
                        },
                        "result": None,  # For some reason, TrueNAS has a null result for this...
                        "error": None,
                        "exception": None,
                        "exc_info": None,
                        "state": "SUCCESS",
                        "time_started": datetime.datetime(
                            2021, 1, 7, 21, 30, 0, tzinfo=datetime.timezone.utc
                        ),
                        "time_finished": datetime.datetime(
                            2021, 1, 7, 21, 30, 1, tzinfo=datetime.timezone.utc
                        ),
                    },
                },
            )
            return JOB_ID

        self._server.register_method_handler(
            "jail.stop",
            stop_handler,
        )
        await self._machine.get_jails()
        jail = self._machine.jails[0]

        self.assertTrue(await jail.stop())

    async def test_restart(self) -> None:
        NAME = "jail01"
        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": NAME,
                    "state": "down",
                },
            ],
        )
        await self._machine.get_jails()
        jail = self._machine.jails[0]
        with self.assertRaises(RuntimeError):
            await jail.restart()

        self._server.register_method_handler(
            "jail.query",
            lambda *args: [
                {
                    "id": NAME,
                    "state": "up",
                },
            ],
            override=True,
        )

        def restart_handler(name) -> int:
            JOB_ID = 42
            self.assertEqual(name, NAME)
            self._server.send_subscription_data(
                {
                    "msg": "changed",
                    "collection": "core.get_jobs",
                    "id": JOB_ID,
                    "fields": {
                        "id": JOB_ID,
                        "method": "jail.start",
                        "arguments": [NAME],
                        "logs_path": None,
                        "logs_excerpt": None,
                        "progress": {
                            "percent": 100,
                            "description": None,
                            "extra": None,
                        },
                        "result": True,
                        "error": None,
                        "exception": None,
                        "exc_info": None,
                        "state": "SUCCESS",
                        "time_started": datetime.datetime(
                            2021, 1, 7, 21, 30, 0, tzinfo=datetime.timezone.utc
                        ),
                        "time_finished": datetime.datetime(
                            2021, 1, 7, 21, 30, 1, tzinfo=datetime.timezone.utc
                        ),
                    },
                },
            ),
            return JOB_ID

        self._server.register_method_handler(
            "jail.restart",
            restart_handler,
        )
        await self._machine.get_jails()
        jail = self._machine.jails[0]

        self.assertTrue(await jail.restart())

    def test_eq_impl(self) -> None:
        self._machine._jail_fetcher._state = {"jail01": {"id": "jail01", "state": "up"}}
        a = CachingJail(self._machine._jail_fetcher, "jail01")
        b = CachingJail(self._machine._jail_fetcher, "jail01")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
