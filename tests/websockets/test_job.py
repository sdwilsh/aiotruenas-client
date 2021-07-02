import datetime
import unittest
from unittest import IsolatedAsyncioTestCase

from aiotruenas_client.job import JobStatus
from aiotruenas_client.websockets import CachingMachine
from tests.fakes.fakeserver import TrueNASServer


class TestJob(IsolatedAsyncioTestCase):
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
        JOB_ID = 42
        self._server.register_method_handler(
            "core.get_jobs",
            lambda *args: [
                {
                    "arguments": ["jail01"],
                    "error": None,
                    "exc_info": None,
                    "exception": None,
                    "id": JOB_ID,
                    "logs_excerpt": None,
                    "logs_path": None,
                    "method": "jail.start",
                    "progress": {"description": None, "extra": None, "percent": None},
                    "result": None,
                    "state": "RUNNING",
                    "time_finished": None,
                    "time_started": datetime.datetime(
                        2021, 1, 6, 17, 51, 29, 741000, tzinfo=datetime.timezone.utc
                    ),
                },
            ],
        )

        job = await self._machine.get_job(42)
        self.assertEqual(job.id, JOB_ID)
        self.assertEqual(job.method, "jail.start")
        self.assertEqual(job.status, JobStatus.RUNNING)

    async def test_success_data_interpretation(self) -> None:
        JOB_ID = 42
        self._server.register_method_handler(
            "core.get_jobs",
            lambda *args: [
                {
                    "arguments": ["jail01"],
                    "error": None,
                    "exc_info": None,
                    "exception": None,
                    "id": JOB_ID,
                    "logs_excerpt": None,
                    "logs_path": None,
                    "method": "jail.start",
                    "progress": {"description": None, "extra": None, "percent": 100},
                    "result": True,
                    "state": "SUCCESS",
                    "time_finished": datetime.datetime(
                        2021, 1, 6, 17, 51, 41, 281000, tzinfo=datetime.timezone.utc
                    ),
                    "time_started": datetime.datetime(
                        2021, 1, 6, 17, 51, 29, 741000, tzinfo=datetime.timezone.utc
                    ),
                }
            ],
        )

        job = await self._machine.get_job(42)
        self.assertEqual(job.id, JOB_ID)
        self.assertEqual(job.method, "jail.start")
        self.assertEqual(job.result, True)
        self.assertEqual(job.status, JobStatus.SUCCESS)

    async def test_failed_data_interpretation(self) -> None:
        JOB_ID = 42
        self._server.register_method_handler(
            "core.get_jobs",
            lambda *args: [
                {
                    "arguments": ["jail01"],
                    "error": "[EFAULT] jail01 is not running",
                    "exc_info": {"extra": None, "type": "CallError"},
                    "exception": "Traceback (most recent call last):...",
                    "id": JOB_ID,
                    "logs_excerpt": None,
                    "logs_path": None,
                    "method": "jail.stop",
                    "progress": {"description": None, "extra": None, "percent": None},
                    "result": None,
                    "state": "FAILED",
                    "time_finished": datetime.datetime(
                        2021, 1, 6, 5, 22, 38, 286000, tzinfo=datetime.timezone.utc
                    ),
                    "time_started": datetime.datetime(
                        2021, 1, 6, 5, 22, 37, 945000, tzinfo=datetime.timezone.utc
                    ),
                }
            ],
        )

        job = await self._machine.get_job(42)
        self.assertEqual(job.error, "[EFAULT] jail01 is not running")
        self.assertEqual(job.id, JOB_ID)
        self.assertEqual(job.method, "jail.stop")
        self.assertEqual(job.status, JobStatus.FAILED)

    async def test_waiting_data_interpretation(self) -> None:
        JOB_ID = 42
        self._server.register_method_handler(
            "core.get_jobs",
            lambda *args: [
                {
                    "arguments": ["jail01"],
                    "error": None,
                    "exc_info": None,
                    "exception": None,
                    "id": JOB_ID,
                    "logs_excerpt": None,
                    "logs_path": None,
                    "method": "jail.stop",
                    "progress": {"description": None, "extra": None, "percent": None},
                    "result": None,
                    "state": "WAITING",
                    "time_finished": None,
                    "time_started": datetime.datetime(
                        2021, 1, 6, 18, 8, 38, 561000, tzinfo=datetime.timezone.utc
                    ),
                },
            ],
        )

        job = await self._machine.get_job(42)
        self.assertEqual(job.id, JOB_ID)
        self.assertEqual(job.method, "jail.stop")
        self.assertEqual(job.status, JobStatus.WAITING)


if __name__ == "__main__":
    unittest.main()
