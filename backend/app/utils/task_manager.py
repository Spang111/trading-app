"""
Background task tracking for graceful shutdown.

We avoid "fire-and-forget" tasks that may get silently dropped on SIGTERM.
Instead we track tasks and:
- log exceptions from background tasks
- wait for completion on shutdown (with a timeout)
- cancel any remaining tasks after timeout
"""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Optional, Set

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self) -> None:
        self._tasks: Set[asyncio.Task] = set()

    def create_task(self, coro: Awaitable, *, name: Optional[str] = None) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        task.add_done_callback(self._log_task_exception)
        return task

    def task_count(self) -> int:
        return len(self._tasks)

    def _log_task_exception(self, task: asyncio.Task) -> None:
        try:
            exc = task.exception()
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("Failed to read background task exception.")
            return
        if exc is not None:
            logger.exception("Background task failed.", exc_info=exc)

    async def shutdown(self, *, timeout_seconds: float = 10.0) -> None:
        if not self._tasks:
            return

        tasks = set(self._tasks)
        done, pending = await asyncio.wait(tasks, timeout=timeout_seconds)
        _ = done  # (done tasks are removed via callbacks)

        if not pending:
            return

        logger.warning("Cancelling %d background task(s) on shutdown.", len(pending))
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

