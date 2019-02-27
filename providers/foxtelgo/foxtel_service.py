import sys
from enum import Enum
import asyncio
import traceback
# from contextlib import suppress
from support.xvfb import XvfbAsync
from support.x11vnc import X11vncAsync
from support.ffmpeg import FFMpeg
# from .timer import Timer
from .foxtel import Foxtel
import logging


logger = logging.getLogger(__name__)


class FoxtelService:
    class State(Enum):
        Off = 0
        Idle = 1
        Playing = 2
        Recording = 3

    class Event(Enum):
        Start = 0
        StartPlay = 1
        StartRecord = 2
        StopRecord = 3
        StopPlay = 4
        Stop = 5
        Reload = 6
        Restart = 7

    def __init__(self):
        self._running = False
        self._lock = asyncio.Lock()
        self._xvfb = None
        self._x11vnc = None
        self._x11vnc_task = None
        self._foxtel = None
        self._ffmpeg = None
        self._current_channel = ''
        self._states = {
            self.State.Off: self._state_off,
            self.State.Idle: self._state_idle,
            self.State.Playing: self._state_playing,
            self.State.Recording: self._state_recording,
        }
        self._state = self.State.Off
        # self._event_q = asyncio.Queue()
        # self._response_q = asyncio.Queue()
        # self._task = asyncio.create_task(self._state_machine())

    async def _action_start(self):
        self._xvfb = XvfbAsync(option_list=[
            '-ac',
            '-extension', "RANDR",
            '-extension', "RENDER",
            '-extension', "GLX"],
            width=1280, height=720, colordepth=24)
        await self._xvfb.start()
        self._x11vnc = X11vncAsync(self._xvfb.new_display)
        self._x11vnc_task = asyncio.create_task(self._x11vnc.start())
        self._foxtel = Foxtel()
        self._ffmpeg = FFMpeg()
        self._current_channel = ''
        await self._foxtel.start()
        await self._foxtel.change_page(Foxtel.State.HOME)

    async def _action_stop(self):
        if self._ffmpeg is not None:
            logger.info('ffmpeg stop')
            await self._ffmpeg.stop()
            self._ffmpeg = None
        if self._foxtel is not None:
            logger.info('foxtel stop')
            await self._foxtel.stop()
            self._foxtel = None
        if self._x11vnc is not None:
            logger.info('x11vnc stop')
            await self._x11vnc.stop()
            self._x11vnc = None
        if self._x11vnc_task is not None:
            logger.info('x11vnc_task stop')
            await self._x11vnc_task
            self._x11vnc_task = None
        if self._xvfb is not None:
            logger.info('xvfb stop')
            await self._xvfb.stop()
            self._xvfb = None

    async def _action_start_playing1(self):
        await self._foxtel.change_page(Foxtel.State.LIVETV)

    async def _action_start_playing2(self):
        await self._foxtel.change_page(Foxtel.State.FSLIVETV)

    async def _action_start_recording(self):
        if not self._ffmpeg._running:
            await self._ffmpeg.start()

    async def _action_stop_playing(self):
        await self._foxtel.change_page(Foxtel.State.LIVETV)
        await self._foxtel.change_page(Foxtel.State.HOME)

    async def _action_stop_recording(self):
        if self._ffmpeg._running:
            await self._ffmpeg.stop()

    async def _action_reload(self):
        await self._foxtel.reload()

    async def _action_restart(self):
        await self._foxtel.restart()

    async def _action_channel(self, args):
        if args:
            await self._foxtel.change_channel(args[0])
            self._current_channel = args[0]

    async def _state_off(self, event):
        if event[0] == self.Event.Start:
            await self._action_start()
            self._state = self.State.Idle
            return
        if event[0] == self.Event.StartPlay:
            await self._action_start()
            self._state = self.State.Idle
            await self._action_start_playing1()
            await self._action_channel(event[1:])
            await self._action_start_playing2()
            self._state = self.State.Playing
            return
        if event[0] == self.Event.StartRecord:
            await self._action_start()
            self._state = self.State.Idle
            await self._action_start_playing1()
            await self._action_channel(event[1:])
            await self._action_start_playing2()
            self._state = self.State.Playing
            await self._action_start_recording()
            self._state = self.State.Recording
            return

    async def _state_idle(self, event):
        if event[0] == self.Event.StartPlay:
            await self._action_start_playing1()
            await self._action_channel(event[1:])
            await self._action_start_playing2()
            self._state = self.State.Playing
            return
        if event[0] == self.Event.StartRecord:
            await self._action_start_playing1()
            await self._action_channel(event[1:])
            await self._action_start_playing2()
            self._state = self.State.Playing
            await self._action_start_recording()
            self._state = self.State.Recording
            return

        if event[0] == self.Event.Stop:
            await self._action_stop()
            self._state = self.State.Off

        if event[0] == self.Event.Restart:
            await self._action_restart()
            return

    async def _state_playing(self, event):
        if event[0] == self.Event.StartPlay:
            if event[1:]:
                await self._action_start_playing1()
                await self._action_channel(event[1:])
                await self._action_start_playing2()
            # await self._action_channel(event[1:])
            return

        if event[0] in [self.Event.StartRecord]:
            await self._action_start_recording()
            if event[1:]:
                if self._current_channel != event[1]:
                    await self._action_start_playing1()
                    await self._action_channel(event[1:])
                    await self._action_start_playing2()
            # await self._action_channel(event[1:])
            self._state = self.State.Recording
            return

        if event[0] == self.Event.StopPlay:
            await self._action_stop_playing()
            self._state = self.State.Idle
            return

        if event[0] == self.Event.Stop:
            await self._action_stop()
            self._state = self.State.Off
            return

        if event[0] == self.Event.Reload:
            await self._action_reload()
            return

        if event[0] == self.Event.Restart:
            await self._action_restart()
            return

    async def _state_recording(self, event):
        if event[0] == self.Event.StartRecord:
            if event[1:]:
                if self._current_channel != event[1]:
                    await self._action_start_playing1()
                    await self._action_channel(event[1:])
                    await self._action_start_playing2()
            # await self._action_channel(event[1:])
            return

        if event[0] == self.Event.StartPlay:
            await self._action_stop_recording()
            self._state = self.State.Playing
            if event[1:]:
                if self._current_channel != event[1]:
                    await self._action_start_playing1()
                    await self._action_channel(event[1:])
                    await self._action_start_playing2()
            # await self._action_channel(event[1:])
            return

        if event[0] == self.Event.Stop:
            await self._action_stop_recording()
            self._state = self.State.Playing
            await self._action_stop()
            self._state = self.State.Off
            return

        if event[0] == self.Event.StopRecord:
            await self._action_stop_recording()
            self._state = self.State.Playing
            return

        if event[0] == self.Event.StopPlay:
            await self._action_stop_recording()
            self._state = self.State.Playing
            await self._action_stop_playing()
            self._state = self.State.Idle
            return

        if event[0] == self.Event.Reload:
            await self._action_reload()
            return

        if event[0] == self.Event.Restart:
            await self._action_restart()
            return

    async def process_event(self, *event):
        async with self._lock:
            # noinspection PyBroadException
            try:
                prev_state = self._state
                await self._states[self._state](event)
                logger.info(f"Event {event}: state {prev_state} -> {self._state}")
            except Exception:
                # noinspection PyUnusedLocal
                current_state = self._state     # this appears in the web trace
                logger.info(f"Exception in state {self._state} happened for event {event}", exc_info=1)
                # traceback.print_exc(stdofile=sys.ut)
                with open('page_dump.html', 'w') as f:
                    traceback.print_exc(file=f)
                    f.write(await self._foxtel.page.content())
            finally:
                pass

    async def get_channels(self):
        revert = False
        if self._state not in [self.State.Playing, self.State.Recording]:
            await self.process_event(self.Event.StartPlay)
            revert = True
        channel_name_elements = await self._foxtel.page.xpath('//div[@class="channel-image"]/img')
        # nchannels = len(channel_names)
        # logger.info(f"Channels: {nchannels}")
        channel_names = []
        for channel in channel_name_elements:
            # cname = await channel.innerText
            channel_names.append(await(await channel.getProperty('alt')).jsonValue())
        if revert:
            await self.process_event(self.Event.StopPlay)
        return channel_names

    @property
    def state(self):
        return self._state

    async def _cleanup(self):
        pass

    async def stop(self):
        await self.process_event(self.Event.Stop)
        # self._task.cancel()
        # with suppress(asyncio.CancelledError):
        #     await self._task
        # self._running = False
        await self._cleanup()
