import os
import asyncio
import logging


logger = logging.getLogger(__name__)


class FFMpeg:
    FRAMERATE = 50
    # FRAMERATE=25
    # THREAD_QUEUE = ""

    # PROFILE=high
    PROFILE = "high444"
    # PROFILE=baseline
    # PIXFMT="-pix_fmt yuv420p"
    PIXFMT = ""
    # TUNE="-tune zerolatency"
    TUNE = ""
    GOP = ""
    THREAD_QUEUE = "-thread_queue_size 32"
    # OUTPUT_FRAMERATE = "-r 25"
    OUTPUT_FRAMERATE = ""
    IPADDR = "192.168.1.1:55555"
    PRESET = "medium"
    BUFSIZE = 65535
    # TIMESTAMP = '-use_wallclock_as_timestamps 1'
    TIMESTAMP = ''

    PROGRAM = f'ffmpeg {TIMESTAMP} -re -f x11grab -video_size 1280x720 -framerate {FRAMERATE} ' \
        f'{THREAD_QUEUE} -i :99.0+0,0 {TIMESTAMP} -f alsa -ac 2 -ar 48000 -i plughw:Loopback,1,0 ' \
        f'{PIXFMT} -c:v libx264 -crf 21 {GOP} -preset {PRESET} -profile {PROFILE} {TUNE} ' \
        f'-bufsize 10000k {OUTPUT_FRAMERATE} -c:a aac -b:a 320k -vsync 1 -y -threads 0 ' \
        f'-flush_packets 0 -f mpegts udp://{IPADDR}?pkt_size=1316&buffer_size={BUFSIZE}'
    PROGRAM = PROGRAM.split()

    def __init__(self):
        self._running = False
        self._proc = None
        self._task = None
        # print(f"ffmpeg {self.PROGRAM}")

    async def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def _run(self):
        self._running = True
        env = os.environ.copy()
        env['DISPLAY'] = ":99"
        with open(os.devnull, 'w') as fnull:
            while self._running:
                logger.info(f"starting ffmpeg")
                # logger.info(f"starting ffmpeg {self.PROGRAM}")
                try:
                    self._proc = await asyncio.create_subprocess_exec(*self.PROGRAM,
                                                                      env=env,
                                                                      stdout=fnull,
                                                                      stderr=fnull,
                                                                      close_fds=True)
                    await self._proc.wait()
                    if self._proc.returncode == 255 and not self._running:
                        logger.info(f'ffmpeg was terminated successfully')
                    elif self._proc.returncode != 0:
                        logger.info(f'ffmpeg failed with return code {self._proc.returncode}')
                        if self._proc.returncode != -11 and self._proc.returncode != -4:
                            self._running = False
                        else:
                            # if the return code is 11 (segfault) then wait and restart
                            await asyncio.sleep(1)
                except Exception as ex:
                    logger.info('ffmpeg exception {ex}', exc_info=1)
                    await asyncio.sleep(2)
                    self._running = False
                finally:
                    self._proc = None
                logger.info("done ffmpeg running=%s" % self._running)

        self._running = False

    async def stop(self):
        if self._running:
            self._running = False
        if self._proc is not None:
            try:
                self._proc.terminate()
            except (RuntimeError, ProcessLookupError):
                pass
        if self._task is not None:
            await self._task
            self._task = None

    async def __aenter__(self):
        """used by the :keyword:`with` statement"""
        await self.start()
        return self

    async def __aexit__(self, *exc_info):
        """used by the :keyword:`with` statement"""
        await self.stop()
