import os
import asyncio
import logging


logger = logging.getLogger(__name__)


class X11vncAsync:

    def __init__(self, display):
        super(X11vncAsync, self).__init__()
        self.display = str(display)
        self.running = False
        self.proc = None

    async def stop(self):
        self.running = False
        if self.proc:
            try:
                self.proc.terminate()
            except RuntimeError:
                pass

    async def start(self):
        env = os.environ.copy()
        env['DISPLAY'] = ":%s" % self.display
        self.running = True
        while self.running:
            logger.info("starting x11vnc %s" % self.display)
            fnull = open(os.devnull, 'w')
            self.proc = await asyncio.create_subprocess_exec('x11vnc', env=env, stdout=fnull,
                                                             stderr=fnull, close_fds=True)
            try:
                await self.proc.wait()
            finally:
                fnull.close()
            logger.info("done x11vnc running=%s" % self.running)
        self.running = False

    async def __aenter__(self):
        """used by the :keyword:`with` statement"""
        await self.start()
        return self

    async def __aexit__(self, *exc_info):
        """used by the :keyword:`with` statement"""
        await self.stop()
