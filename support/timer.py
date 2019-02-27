import asyncio
from contextlib import suppress
from typing import Any, Awaitable, Callable, Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


class Timer:
    def __init__(self, timeout=None, callback=None):
        self._task = None
        self._callback = None
        # logger.info('Timer.__init__')
        if timeout is not None and callback is not None:
            # noinspection PyTypeChecker
            self.start(timeout, callback)
        # else:
        #     logger.error(f'Timer invalid timeout={timeout} callback={callback}')

    def start(self, timeout, callback):
        # logger.info('Timer.start')
        self._task = asyncio.create_task(self._job(timeout, callback, self._task))

    # noinspection PyMethodMayBeStatic
    async def _job(self, timeout, callback, prev_task):
        # logger.info("timer job start")
        try:
            if prev_task is not None and not prev_task.done():
                prev_task.cancel()
                # print("timer job cancel 1")
                with suppress(asyncio.CancelledError):
                    await prev_task
                    # logger.info("timer job cancel 2")

            await asyncio.sleep(timeout)
            # logger.info("timer job sleep done")

            await callback
        except asyncio.CancelledError:
            # logger.info("timer job callback cancelled")
            callback.close()
            # logger.info("timer job callback cancelled complete")
        except Exception:
            logger.exception('Exception in Timer task')
        finally:
            self._task = None
            # logger.info("timer job callback done")

    async def cancel(self):
        if self._task is not None:
            if not self._task.done():
                await asyncio.sleep(0)   # let task start if it hasn't already
                self._task.cancel()
                with suppress(asyncio.CancelledError):
                   await self._task
            self.task = None
