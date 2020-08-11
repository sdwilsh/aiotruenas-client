import unittest

from unittest import IsolatedAsyncioTestCase
from pyfreenas import Machine
from pyfreenas.virtualmachine import VirturalMachine, VirturalMachineState
from tests.fakes.fakeserver import FreeNASServer


class TestVirturalMachine(IsolatedAsyncioTestCase):
    _server: FreeNASServer
    _machine: Machine

    def setUp(self):
        self._server = FreeNASServer()
        self._server.register_method_handler(
            "disk.query", lambda *args: [],
        )
        self._server.register_method_handler(
            "disk.temperatures", lambda *args: {},
        )

    async def asyncSetUp(self):
        self._machine = await Machine.create(
            self._server.host,
            username=self._server.username,
            password=self._server.password,
        )

    async def asyncTearDown(self):
        await self._machine.close()
        await self._server.stop()

    async def test_running_data_interpretation(self) -> None:
        DESCRIPTION = "Some Desc"
        ID = 1
        NAME = "vm01"
        self._server.register_method_handler(
            "vm.query",
            lambda *args: [
                {
                    "description": DESCRIPTION,
                    "id": ID,
                    "name": NAME,
                    "status": {"pid": 42, "state": "RUNNING"},
                },
            ],
        )

        await self._machine.refresh()

        self.assertEqual(len(self._machine.vms), 1)
        vm = self._machine.vms[0]
        self.assertEqual(vm.description, DESCRIPTION)
        self.assertEqual(vm.id, ID)
        self.assertEqual(vm.name, NAME)
        self.assertEqual(vm.status, VirturalMachineState.RUNNING)

    async def test_stopped_data_interpretation(self) -> None:
        DESCRIPTION = ""
        ID = 3
        NAME = "vm02"
        self._server.register_method_handler(
            "vm.query",
            lambda *args: [
                {
                    "description": DESCRIPTION,
                    "id": ID,
                    "name": NAME,
                    "status": {"pid": None, "state": "STOPPED"},
                },
            ],
        )

        await self._machine.refresh()

        self.assertEqual(len(self._machine.vms), 1)
        vm = self._machine.vms[0]
        self.assertEqual(vm.description, DESCRIPTION)
        self.assertEqual(vm.id, ID)
        self.assertEqual(vm.name, NAME)
        self.assertEqual(vm.status, VirturalMachineState.STOPPED)

    async def test_availability(self) -> None:
        self._server.register_method_handler(
            "vm.query",
            lambda *args: [
                {
                    "description": "Some Desc",
                    "id": 1,
                    "name": "vm01",
                    "status": {"pid": 42, "state": "RUNNING"},
                },
            ],
        )

        await self._machine.refresh()

        vm = self._machine.vms[0]
        self.assertTrue(vm.available)

        self._server.register_method_handler(
            "vm.query", lambda *args: [], override=True,
        )
        await self._machine.refresh()
        self.assertFalse(vm.available)
        self.assertEqual(len(self._machine.vms), 0)

    async def test_unavailable_caching(self) -> None:
        """Certain properites have caching even if no longer available"""
        DESCRIPTION = "Some Desc"
        ID = 1
        NAME = "vm01"
        self._server.register_method_handler(
            "vm.query",
            lambda *args: [
                {
                    "description": DESCRIPTION,
                    "id": ID,
                    "name": NAME,
                    "status": {"pid": 42, "state": "RUNNING"},
                },
            ],
        )
        await self._machine.refresh()
        vm = self._machine.vms[0]
        assert vm is not None
        self._server.register_method_handler(
            "vm.query", lambda *args: [], override=True,
        )
        await self._machine.refresh()

        self.assertEqual(vm.description, DESCRIPTION)
        self.assertEqual(vm.id, ID)
        self.assertEqual(vm.name, NAME)
        with self.assertRaises(AssertionError):
            vm.status

    async def test_same_instance_after_refresh(self) -> None:
        self._server.register_method_handler(
            "vm.query",
            lambda *args: [
                {
                    "description": "Some Desc",
                    "id": 1,
                    "name": "vm01",
                    "status": {"pid": 42, "state": "RUNNING"},
                },
            ],
        )
        await self._machine.refresh()
        original_vm = self._machine.vms[0]
        await self._machine.refresh()
        new_vm = self._machine.vms[0]
        self.assertIs(original_vm, new_vm)

    async def test_start(self) -> None:
        ID = 42
        self._server.register_method_handler(
            "vm.query",
            lambda *args: [
                {
                    "description": "Some Desc",
                    "id": 42,
                    "name": "vm01",
                    "status": {"pid": None, "state": "STOPPED"},
                },
            ],
        )

        def start_handler(id, kwargs) -> None:
            self.assertEqual(id, ID)
            self.assertFalse(kwargs["overcommit"])
            return None

        self._server.register_method_handler(
            "vm.start", start_handler,
        )
        await self._machine.refresh()
        vm = self._machine.vms[0]
        assert vm is not None

        self.assertEqual(await vm.start(), None)

    async def test_stop(self) -> None:
        ID = 42
        self._server.register_method_handler(
            "vm.query",
            lambda *args: [
                {
                    "description": "Some Desc",
                    "id": 42,
                    "name": "vm01",
                    "status": {"pid": 10, "state": "RUNNING"},
                },
            ],
        )

        def stop_handler(id, force) -> bool:
            self.assertEqual(id, ID)
            self.assertFalse(force)
            return True

        self._server.register_method_handler(
            "vm.stop", stop_handler,
        )
        await self._machine.refresh()
        vm = self._machine.vms[0]
        assert vm is not None

        self.assertTrue(await vm.stop())

    async def test_restart(self) -> None:
        ID = 42
        self._server.register_method_handler(
            "vm.query",
            lambda *args: [
                {
                    "description": "Some Desc",
                    "id": 42,
                    "name": "vm01",
                    "status": {"pid": 10, "state": "RUNNING"},
                },
            ],
        )

        def restart_handler(id) -> bool:
            self.assertEqual(id, ID)
            return True

        self._server.register_method_handler(
            "vm.restart", restart_handler,
        )
        await self._machine.refresh()
        vm = self._machine.vms[0]
        assert vm is not None

        self.assertTrue(await vm.restart())


if __name__ == "__main__":
    unittest.main()
