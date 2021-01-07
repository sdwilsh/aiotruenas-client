import asyncio
import logging
from typing import Any, Dict, Optional, TypeVar

from ..job import Job, JobStatus, TJobId
from .interfaces import StateFetcher, Subscriber, WebsocketMachine

TCachingJobFetcher = TypeVar("TCachingJobFetcher", bound="CachingJobFetcher")

logger = logging.getLogger(__name__)


class CachingJob(Job):
    def __init__(
        self,
        fetcher: TCachingJobFetcher,
        id: TJobId,
        method: str,
    ) -> None:
        super().__init__(id=id, method=method)
        self._fetcher = fetcher
        self._cached_state = self._state

    @property
    def error(self) -> Optional[str]:
        """The error message from the API."""
        return self._state["error"]

    @property
    def result(self) -> Optional[Any]:
        """The result of the job."""
        return self._state["result"]

    @property
    def status(self) -> JobStatus:
        """The state of the job."""
        return JobStatus.fromValue(self._state["state"])

    @property
    def _state(self) -> Dict[str, Any]:
        """The state of the job, according to the fetcher."""
        return self._fetcher._get_cached_state(self)


class CachingJobFetcher(StateFetcher, Subscriber):
    _parent: WebsocketMachine
    # This is probably not the best approach, as this will grow unbounded over time...
    _state: Dict[TJobId, Dict[str, Any]]
    _subscription_task: asyncio.Task

    def __init__(self, machine: WebsocketMachine) -> None:
        self._parent = machine
        self._state = {}

    @classmethod
    async def create(
        cls,
        machine: WebsocketMachine,
    ) -> TCachingJobFetcher:
        cjf = CachingJobFetcher(machine=machine)
        queue = await machine._subscribe(cjf, "core.get_jobs")
        cjf._subscription_task = asyncio.create_task(
            cjf._subscription_queue_processor(queue)
        )
        return cjf

    async def unsubscribe(self) -> None:
        self._subscription_task.cancel()
        await self._parent._unsubscribe(self, "core.get_jobs")

    async def get_job(self, id: TJobId) -> CachingJob:
        if id not in self._state:
            jobs = await self._parent._invoke_method("core.get_jobs", ["id", "=", id])
            self._state[id] = jobs[0]

        return CachingJob(fetcher=self, id=id, method=self._state[id]["method"])

    def _get_cached_state(self, job: Job) -> Dict[str, Any]:
        return self._state[job.id]

    async def _subscription_queue_processor(self, queue: asyncio.Queue) -> None:
        try:
            while True:
                item = await queue.get()
                self._state[item["id"]] = item["fields"]
                queue.task_done()
        except asyncio.CancelledError:
            logger.debug(
                "core.get_jobs subscription work processing is getting canceled"
            )
            raise
        except Exception as exc:
            logger.exception(
                "exception while processing core.get_jobs data", exc_info=exc
            )
