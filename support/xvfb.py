import os
import asyncio
from xvfbwrapper import Xvfb
import logging


logger = logging.getLogger(__name__)


class XvfbAsync(Xvfb):
    def __init__(self, **kwargs):
        option_list = kwargs['option_list']
        del kwargs['option_list']
        super(XvfbAsync, self).__init__(**kwargs)
        self.extra_xvfb_args.extend(option_list)
        self.new_display = None
        self.xvfb_cmd = None
        self.fnull = None
        # self.proc = None

    def _get_next_unused_display(self):
        import fcntl
        tempfile_path = os.path.join(self._tempdir, '.X{0}-lock')
        rand = 99
        while True:
            self._lock_display_file = open(tempfile_path.format(rand), 'w')
            try:
                fcntl.flock(self._lock_display_file,
                            fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                rand += 1
                continue
            else:
                return rand
        return 99

    async def start(self):
        self.new_display = self._get_next_unused_display()
        display_var = ':{}'.format(self.new_display)
        self.xvfb_cmd = ['Xvfb', display_var] + self.extra_xvfb_args
        self.fnull = open(os.devnull, 'w')
        self.proc = await asyncio.create_subprocess_exec(*self.xvfb_cmd,
                                                         stdout=self.fnull,
                                                         stderr=self.fnull,
                                                         close_fds=True)
        # give Xvfb time to start
        await asyncio.sleep(self.__class__.SLEEP_TIME_BEFORE_START)
        self._set_display_var(self.new_display)
        # ret_code = self.proc.poll()
        # if ret_code is None:
        #     self._set_display_var(self.new_display)
        # else:
        #     self._cleanup_lock_file()
        #     raise RuntimeError('Xvfb did not start')

    async def stop(self):
        try:
            if self.orig_display is None:
                del os.environ['DISPLAY']
            else:
                self._set_display_var(self.orig_display)
            if self.proc is not None:
                try:
                    self.proc.terminate()
                    await self.proc.wait()
                    self.fnull.close()
                except OSError:
                    pass
                self.proc = None
        finally:
            self._cleanup_lock_file()
