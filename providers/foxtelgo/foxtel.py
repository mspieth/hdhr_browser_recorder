import sys
import os
import asyncio
from enum import Enum
import logging
from support.timer import Timer
from datetime import datetime

if __name__ != '__main__':
    config = sys.modules['__main__'].config


def patch_pyppeteer():
    """
    fixes disconenction issue #159
    https://github.com/miyakogi/pyppeteer/pull/160
    """
    import websockets
    if float(websockets.__version__) >= 7.0:
        import pyppeteer.connection
        original_method = pyppeteer.connection.websockets.client.connect

        def new_method(*args, **kwargs):
            kwargs['ping_interval'] = None
            kwargs['ping_timeout'] = None
            return original_method(*args, **kwargs)

        pyppeteer.connection.websockets.client.connect = new_method


patch_pyppeteer()
from pyppeteer import launcher
from pyppeteer.errors import *
from pyppeteer.launcher import Launcher

logger = logging.getLogger(__name__)


'''
Data

channel
#root > div > div > div.content.live > span > div > div.channels-container > 
    div.channels > div > div > div:nth-child(1) > div.top-row > div.channel-image > img
//*[@id="root"]/div/div/div[2]/span/div/div[2]/div[2]/div/div/div[1]/div[1]/div[1]/img
document.querySelector('#root > div > div > div.content.live > span > div > 
    div.channels-container > div.channels > div > div > div:nth-child(1) > div.top-row > div.channel-image > img')
#root > div > div > div.content.live > span > div > div.channels-container > div.channels > 
    div > div > div:nth-child(4) > div.top-row > div.channel-image > img
//*[@id="root"]/div/div/div[2]/span/div/div[2]/div[2]/div/div/div[4]/div[1]/div[1]/img

fullscreen toggle from windowed livetv
#player > div > div.overlay.hide-cursor.quarter-screen > span > div.bottom-bar > 
    div.bottom-bar-inner.bottom-controls-hider > div.right > span:nth-child(3) > span.fullscreen-toggle
//*[@id="player"]/div/div[2]/span/div[2]/div[2]/div[2]/span[3]/span[1]
<span class="fullscreen-toggle">
<svg width="21px" height="22px" viewBox="0 0 21 22" version="1.1" xmlns="http://www.w3.org/2000/svg">
<title>Enter Fullscreen</title>
<g id="Video-Player-Desktop" stroke="none" stroke-width="1" fill="none" 
    fill-rule="evenodd" stroke-linecap="round" stroke-linejoin="round">
<g id="Video-player---VOD-TV---Volume" transform="translate(-1293.000000, -723.000000)" stroke="#FFFFFF">
<g id="Lower-controls" transform="translate(50.000000, 682.000000)">
<g id="full-screen-icon-desktop" transform="translate(1243.000000, 41.000000)">
<g transform="translate(-1.000000, 0.000000)"><g id="Group-Copy" 
    transform="translate(4.000000, 19.000000) rotate(-180.000000) translate(-4.000000, -19.000000) 
        translate(1.000000, 16.000000)" stroke-width="2">
<path d="M5,6 L5,1" id="Line"></path><path d="M4.4408921e-16,1 L5,1" id="Line"></path></g>
<g id="Group-Copy-2" transform="translate(19.000000, 3.000000) rotate(-360.000000) 
    translate(-19.000000, -3.000000) translate(16.000000, 0.000000)" stroke-width="2">
<path d="M5,6 L5,1" id="Line"></path>
<path d="M0,1 L5,1" id="Line"></path></g>
<g id="Group-Copy-4" transform="translate(4.000000, 3.000000) rotate(-90.000000) 
    translate(-4.000000, -3.000000) translate(1.000000, 0.000000)" stroke-width="2">
<path d="M5,6 L5,1" id="Line"></path>
<path d="M-8.8817842e-16,1 L5,1" id="Line">
</path></g><g id="Group-Copy-3" transform="translate(19.000000, 19.000000) 
    rotate(-270.000000) translate(-19.000000, -19.000000) translate(16.000000, 16.000000)" stroke-width="2">
<path d="M5,6 L5,1" id="Line"></path><path d="M0,1 L5,1" id="Line"></path></g></g></g></g></g></g></svg></span>
#player > div > div.overlay.hide-cursor.quarter-screen > span > div.bottom-bar > 
    div.bottom-bar-inner.bottom-controls-hider > div.right > span:nth-child(3) > span.fullscreen-toggle > svg > title
  title == 'Enter Fullscreen'

Exit Fullscreen
#player > div > div.overlay.hide-cursor.quarter-screen.fullscreen > span > div.bottom-bar > 
    div.bottom-bar-inner.bottom-controls-hider > div.right > span:nth-child(3) > span.fullscreen-toggle > svg > title
//*[@id="player"]/div/div[2]/span/div[3]/div[2]/div[2]/span[3]/span[1]/svg/title
    title == 'Exit Fullscreen'

'''


class Launcher1(Launcher):
    def __init__(self, *cwargs, **kwargs):
        super().__init__(*cwargs, **kwargs)
        self.chromeArguments.remove('--user-data-dir-fake=xxx')
        self.cmd.remove('--user-data-dir-fake=xxx')

    # not needed for git dev branch but needed for 0.0.25
    def _parse_args(self) -> None:
        if isinstance(self.options.get('args'), list):
            self.chrome_args.extend(self.options['args'])

    async def killChrome(self) -> None:
        """Terminate chromium process."""
        logger.info('terminate chrome process...')
        launcher.logger.info('terminate chrome process...')
        if self.connection and self.connection._connected:
            try:
                await self.connection.send('Browser.close')
                await self.connection.dispose()
            except Exception as e:
                # ignore errors on browser termination process
                launcher.debugError(launcher.logger, e)
                logger.info('terminate chrome process exception')
        # if self.temporaryUserDataDir and os.path.exists(self.temporaryUserDataDir):  # noqa: E501
        # Force kill chrome only when using temporary userDataDir
        self.waitForChromeToClose()
        # self._cleanup_tmp_user_data_dir()


async def get_browser():
    env = os.environ.copy()
    env['DISPLAY'] = ":99"
    enable_alsa = 'sudo modprobe snd-aloop pcm_substreams=1'.split(' ')
    with open(os.devnull, 'w') as fnull:
        proc = await asyncio.create_subprocess_exec(*enable_alsa,
                                                    env=env,
                                                    stdout=fnull,
                                                    stderr=fnull,
                                                    close_fds=True)
        await proc.wait()

    # PROG = "google-chrome --remote-debugging-port=9222 -start-maximized --alsa-output-device=hw:Loopback,0,0 https://watch.foxtel.com.au/app"
    return await Launcher1({"headless": False,
                            "args": [
                                '--no-sandbox',
                                # '--disable-setuid-sandbox',
                                '--disable-infobars',
                                '--ignore-certificate-errors',
                                '-start-maximized',
                                '--disable-extensions',
                                # '-start-fullscreen',
                                '--alsa-output-device=hw:Loopback,0,0',
                                '--use-gl',
                                # '--window-size=1280,720',
                                # '--window-position=0,0',
                                '--user-data-dir-fake=xxx',  # to prevent user data dir processing
                            ],
                            # 'dumpio': True,
                            "env": env,
                            "executablePath": '/usr/bin/google-chrome',
                            "ignoreDefaultArgs": True,
                            'autoClose': False,  # do our own chrome management
                            }).launch()


SET_TIMEOUT_TRAP = '''
    // Set up container to hold timeout and interval state
    window.testing = {
      timeouts: {},
      times: {},
      intervals: {}
    };

    // Make a copy of the original setTimeout function
    window._setTimeout = window.setTimeout;
    window.setTimeout = function(callback, timeout) {
      // We need a handle to store our timeout under, we can't just use the
      // timeout ID because we don't know it until after we create the timeout
      var handle = _.uniqueId();

      // Call the old setTimeout function
      var timeoutId;
      # if (timeout === 1800000) {
      #    timeoutId = 10000;
      # } else if (timeout === 10200000) {
      if (timeout === 10200000) {
         timeoutId = 10001;
      } else {
        timeoutId = window._setTimeout(
          function() {
            // The callback is the function we were originally deferring
            callback();

            // Once a timeout completes, we need to remove our reference to it
            delete window.testing.timeouts[handle];
            delete window.testing.times[handle];
          },
          timeout
        );
      }

      // Store the id of the timeout we just created so it can be queried
      window.testing.timeouts[handle] = timeoutId;
      window.testing.times[handle] = timeout;
      return timeoutId;
    };

    // Make a copy of the original clearTimeout function
    window._clearTimeout = window.clearTimeout;
    window.clearTimeout = function(timeoutId) {
      if (timeoutId < 10000) {
        // Call the original clearTimeout function to actually clear the timeout
        var returnValue = window._clearTimeout(timeoutId);
      }

      var timeoutToClear;
      // Look over all the timeouts we have stored and find the one with
      // the timeoutID we just passed in
      _.each(window.testing.timeouts, function(storedTimeoutID, handle) {
        if(storedTimeoutID === timeoutId) {
          timeoutToClear = handle;
        }
      });

      // Delete our stored reference to the timeout
      delete window.testing.timeouts[timeoutToClear];
      delete window.testing.times[timeoutToClear];
      // no return value
    };

    // Make a copy of the original setInterval function
    window._setInterval = window.setInterval;
    window.setInterval = function(cb, interval) {
      // Use the original setInterval function to schedule our interval
      var intervalId = window._setInterval(cb, interval);
      // Store the ID returned by the setInterval call
      window.testing.intervals[intervalId] = interval;
      return intervalId;
    };

    // Make a copy of the original clearInterval function
    window._clearInterval = window.clearInterval;
    window.clearInterval = function(intervalId) {
      // Use the original clearInterval function to clear our interval
      var returnValue = window._clearInterval(intervalId);
      // remove the passed interval ID from our list of IDs
      // window.testing.intervals = _.without(window.testing.intervals, intervalId);
      delete window.testing.intervals[intervalId];
      return returnValue;
    };
'''


class Foxtel(object):

    LOGIN_TITLE = "Foxtel | Login"
    HOME_TITLE = "Foxtel"
    LIVETV_TITLE = "Foxtel | Live TV"
    FULLSCREENLIVETV_TITLE = "Foxtel | Live TV"

    class State(Enum):
        LOGIN = 0
        HOME = 1
        LIVETV = 2
        FSLIVETV = 3

        UNKNOWN = -1

    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
                 '(KHTML, like Gecko) Chrome/69.0.3445.2 Safari/537.36'

    def __init__(self):
        super(Foxtel, self).__init__()
        self.browser = None
        self.page = None
        self.title = ""
        self.state = self.State.LOGIN
        self._heartbeat_timer = Timer()
        self._use_heartbeat = False
        self._reload_timer = Timer()
        self._hover_timer = Timer()
        self._lock = asyncio.Lock()
        self._use_hover = True
        self._use_reload = True
        self._use_squash_timers = True
        self._width = 1280
        self._height = 720
        self.next_state = {
            self.State.LOGIN: {},
            self.State.HOME: {
                self.State.LOGIN: self._login,
                self.State.HOME: self._noop,
                self.State.LIVETV: self._home_menu,
                self.State.FSLIVETV: [self._livetv_exit_fullscreen, self._home_menu],
            },
            self.State.LIVETV: {
                self.State.HOME: self._livetv_menu,
                self.State.LIVETV: self._noop,
                self.State.FSLIVETV: self._livetv_exit_fullscreen,
            },
            self.State.FSLIVETV: {
                self.State.HOME: [self._livetv_menu, self._livetv_enter_fullscreen],
                self.State.LIVETV: self._livetv_enter_fullscreen,
                self.State.FSLIVETV: self._noop,
            },
        }

    async def _update_state(self):
        await asyncio.sleep(0.5)
        self.title = await self.page.title()
        logger.info(f'title is {self.title} url is {self.page.url}')
        self.state = self.State.UNKNOWN
        if self.title == self.LOGIN_TITLE:
            self.state = self.State.LOGIN
        elif self.title == self.HOME_TITLE:
            self.state = self.State.HOME
        elif self.title == self.LIVETV_TITLE:
            fs_toggle_on_windowed = await self.page.querySelector(
                '#player > div > div.quarter-screen')
            # '#player > div > div.overlay.hide-cursor.quarter-screen')
            fs_toggle_on_fullscreen = await self.page.querySelector(
                '#player > div > div.quarter-screen.fullscreen')
            # '#player > div > div.overlay.hide-cursor.quarter-screen.fullscreen')
            if fs_toggle_on_fullscreen:
                logger.info("fs_toggle_on_fullscreen found")
                self.state = self.State.FSLIVETV
            elif fs_toggle_on_windowed:
                logger.info("fs_toggle_on_windowed found")
                self.state = self.State.LIVETV

    async def start(self):
        self.browser = await get_browser()
        self.page = await self.browser.newPage()
        await self.page.setViewport({"width": self._width, "height": self._height})
        await self.page.setUserAgent(self.USER_AGENT)
        if self._use_squash_timers:
            await self.page.evaluateOnNewDocument(
               '''() => {''' + SET_TIMEOUT_TRAP + '''}''')
        await self._reload_page()

    async def _reload_page(self):
        await self.page.goto('https://watch.foxtel.com.au/app', {'waitUntil': 'networkidle2'})
        # await page.keyboard.press('F11')
        # await page.reload({'waitUntil': 'networkidle2'})
        await self._update_state()
        logger.info(f"Initial state is {self.state}")
        await self.show_timeouts()
        self._start_heartbeat()

    def _start_heartbeat(self):
        if self._use_heartbeat:
            try:
                self._heartbeat_timer.start(10.0, self._heatbeat())
            except Exception:
                logger.exception("Exception in heartbeat")
            pass

    async def _stop_heartbeat(self):
        await self._heartbeat_timer.cancel()

    async def _heatbeat(self):
        try:
            if self.page is not None:
                await self.page.querySelector('#root')
            # logger.info('heartbeat')
        except PageError:
            logger.info('heartbeat PageError')
            # pass
        except Exception:
            logger.info(f"Heartbeat exception in {self._state}", exc_info=1)
        self._start_heartbeat()

    def _start_reload_timer(self):
        if self._reload_timer:
            try:
                if self._reload_timer._task is None:
                    self._reload_timer.start(5*3600, self._perform_reload())
                    # self._reload_timer.start(8*3600, self._perform_reload())
                    # self._reload_timer.start(2*60, self._perform_reload())
            except Exception:
                logger.exception("Exception in heartbeat")
            pass

    async def _stop_reload_timer(self):
        if self._reload_timer:
            await self._reload_timer.cancel()

    async def _restart_reload_timer(self):
        if self._reload_timer and self._reload_timer._task is not None:
            await self._reload_timer._task
        self._start_reload_timer()

    async def _perform_reload(self):
        current_state = self.state
        if current_state == self.State.LIVETV:
            current_state = self.State.FSLIVETV
        try:
            async with self._lock:
                logger.info(f'forcing reload in state {current_state}')
                await self._reload_page()
                await self._change_page(current_state)
        except PageError:
            logger.info('reload PageError')
            # pass
        except Exception:
            logger.info(f"Reload exception in {current_state}", exc_info=1)

        asyncio.create_task(self._restart_reload_timer())

    async def _start_hover_timer(self, count=0):
        if not count or count == 0:
            count = 30
        self._hover_timer.start(60, self._hover(count))

    async def _stop_hover_timer(self):
        await self._hover_timer.cancel()

    async def _hover(self, count):
        async with self._lock:
            count -= 1
            if self.page is not None:
                try:
                    if count == 0:
                        logger.info('move mouse')
                        await self.page.mouse.move(self._width - 1, self._height - 1)
                        # await self.page.hover('span.fullscreen-toggle')
                except Exception:
                    logger.exception('hover failed')
                try:
                    failed = False
                    ok_button = await self.page.querySelector('div.buttons:first-child')
                    # in case the ok button is visible, click it
                    if ok_button is not None:
                        logger.info('ok found, clearing dialog')
                        await self.page.click(ok_button)
                except Exception:
                    logger.exception('button click failed 1')
                    failed = True
                try:
                    if failed:
                        ok_button = await self.page.querySelector('div.buttons')
                        # in case the ok button is visible, click it
                        if ok_button is not None:
                            logger.info('ok found, clearing dialog')
                            await self.page.click(ok_button)
                except Exception:
                    logger.exception('button click failed')
        asyncio.create_task(self._start_hover_timer(count))

    async def reload(self):
        await self._stop_reload_timer()
        await self._perform_reload()

    async def restart(self):
        async with self._lock:
            try:
                current_state = self.state
                await self.stop()
                await self.start()
                await self._change_page(current_state)
            except Exception:
                logger.exception('Restart exception')

    async def _check_connection(self):
        ok = False
        try:
            if self.page is not None:
                await self.page.querySelector('#root')
                ok = True
            # logger.info('heartbeat')
        except PageError:
            pass
        except Exception:
            pass
        if not ok:
            logger.info('Connection is down, reconnecting')
            await self.restart()
        return ok

    async def show_timeouts(self):
        # s = await self.page.evaluateHandle('window.testing')
        # s = await s.jsonValue()
        # logger.info(f"timeouts: {s}")
        pass

    async def show_title(self):
        logger.info(f"title is {self.title} state is {self.state}")

    async def _noop(self):
        pass

    async def _click_and_wait(self, button, wait_options=None):
        await self.page.waitForSelector(button, {"timeout": 5000})
        # await asyncio.gather(
        #     self.page.waitForNavigation(options=wait_options or {'waitUntil': 'networkidle0'}),
        #     self.page.click(button)
        # )
        navigation_promise = asyncio.ensure_future(self.page.waitForNavigation(
            options=wait_options or {'waitUntil': 'networkidle0'}))
        await self.page.click(button)
        await navigation_promise

    async def _click_and_wait_element_handle(self, button, wait_options=None):
        # await asyncio.gather(
        #     self.page.waitForNavigation(options=wait_options or {'waitUntil': 'networkidle0'}),
        #     button.click()
        # )
        navigation_promise = asyncio.ensure_future(self.page.waitForNavigation(
            options=wait_options or {'waitUntil': 'networkidle0'}))
        await button.click()
        await navigation_promise

    async def _login(self):
        await self.page.click('input[type="email"]', options={'clickCount': 3})
        await self.page.type('input[type="email"]', config.username)
        await self.page.click('input[type="password"]', options={'clickCount': 3})
        await self.page.type('input[type="password"]', config.password)

        await self._click_and_wait('div.login-box > button')

    async def _home_menu(self):
        if not await self.page.querySelector('#root > div > div > div.menu-bar-container > '
                                             'div > div > div.left-section > div.menu-item.f-menu.active.HOME'):
            # note the word ".active" is inserted just before the menu item if it is the active screen
            await self._click_and_wait(
                '#root > div > div > div.menu-bar-container > '
                'div > div > div.left-section > div.menu-item.f-menu.HOME')
            await self.page.waitForSelector('div.menu-item.f-menu.active.HOME')
            await self.page.waitForSelector('div.menu-item.f-menu.LIVE')
            await self._stop_reload_timer()
            await self._stop_hover_timer()

    async def _livetv_menu(self):
        if not await self.page.querySelector('div.menu-item.f-menu.active.LIVE'):
            # '#root > div > div > div.menu-bar-container > div > div > '\
            # 'div.left-section > div.menu-item.f-menu.active.Live.TV'):
            logger.info('Y')
            await self._click_and_wait('div.menu-item.f-menu.f-menu.LIVE')
            # '#root > div > div > div.menu-bar-container > div > div > '
            # 'div.left-section > div.menu-item.f-menu.Live.TV')
            logger.info('Z')
            await self.page.waitForSelector('div.menu-item.f-menu.active.LIVE')
            logger.info('A')
            await self.page.waitForSelector('#player > div > div.quarter-screen')
            # <g id="Video-player---VOD-movie"
            logger.info('B')
            await self.page.waitForSelector('span.fullscreen-toggle')
            logger.info('C')
            await self.dump_page('livetv1')
            if self._use_reload:
                self._start_reload_timer()
            if self._use_hover:
                await self._start_hover_timer()
        logger.info('X')

    async def _livetv_enter_fullscreen(self):
        # overlay.hide-cursor.
        if await self.page.querySelector('#player > div > div.quarter-screen') and \
           not await self.page.querySelector('#player > div > div.quarter-screen.fullscreen'):
            logger.info("processing enter fs")
            await self.page.waitForSelector('span.fullscreen-toggle')
            logger.info('Y')
            retries_left = 5
            v = None
            while v is None and retries_left > 0:
                await self.page.click('span.fullscreen-toggle')
                # await self._click_and_wait('span.fullscreen-toggle')
                logger.info(f'Z {retries_left}')
                v1 = await self.page.waitForSelector('#player > div > div.quarter-screen.fullscreen', {"timeout": 5000})
                v = await self.page.querySelector('#player > div > div.quarter-screen.fullscreen')
                if (v is None) != (v1 is None):
                    logger.info('selector values are different')
                retries_left -= 1
                if retries_left > 0:
                    await asyncio.sleep(0.5)
            if v is None:
                logger.info('Failed to go to full screen')
            await self.dump_page('livetvfs1')
            # await self.page.waitForSelector('#player > div > div.overlay.hide-cursor.quarter-screen.fullscreen')
        # '#player > div > div.overlay.hide-cursor.quarter-screen > span > div.bottom-bar > '\
        # 'div.bottom-bar-inner.bottom-controls-hider > div.right > span:nth-child(3) > span.fullscreen-toggle')
        logger.info('X')

    async def _livetv_exit_fullscreen(self):
        # overlay.hide-cursor.
        # need to move the mouse to get the page back
        if await self.page.querySelector('#player > div > div.quarter-screen.fullscreen'):
            logger.info("processing exit fs")
            await self.page.click('span.fullscreen-toggle')
            await self.page.waitForSelector('#player > div > div.quarter-screen.fullscreen', options={'hidden': True})
            # await self.page.waitForSelector('#player > div > div.quarter-screen:not(.fullscreen)')
            await self.page.waitForSelector('#player > div > div.quarter-screen')
            # await self.page.waitForSelector('#player > div > div.overlay.hide-cursor.quarter-screen')
        # '#player > div > div.overlay.hide-cursor.quarter-screen.fullscreen > span > div.bottom-bar > ' \
        # 'div.bottom-bar-inner.bottom-controls-hider > div.right > span:nth-child(3) > span.fullscreen-toggle')

    async def change_channel(self, channel):
        logger.info(f"Change channel to '{channel}'")
        async with self._lock:
            try:
                await self._check_connection()
                if self.state in [self.State.LIVETV, self.State.FSLIVETV]:
                    await self._stop_heartbeat()
                    tries = 5
                    while tries > 0:
                        tries -= 1
                        if not await self.page.querySelector(f'div.synopsis-container > div.title-image > img[alt="{channel}."'):
                            # channel_selector = await self.page.xpath(f'//div[@class="channel-image"]/img[@alt="{channel}"]/../../..')
                            channel_selector = await self.page.xpath(f'//div[@class="channel-image"]/img[@alt="{channel}"]/../../..')
                            logger.info(f'channel change selector {channel_selector}')
                            if channel_selector and channel_selector[0]:
                                await asyncio.sleep(1)  # TODO: replace with current channel detection
                                logger.info('clicking...')
                                # await self._click_and_wait_element_handle(channel_selector[0])
                                await channel_selector[0].click(delay=500)
                                try:
                                    # await self.page.xpath(f'//div[@class="synopsis-container"]/div[@class=""]/img[alt=""]')
                                    await self.page.waitForSelector(f'div.synopsis-container > div.title-image > img[alt="{channel}."]',
                                                                    {"timeout":3000})
                                except Exception:
                                    logger.info('failed to click, try again')
                                    continue
                                logger.info('detected changed channel')
                                # await self.page.waitForSelector('#player > div > div.quarter-screen')
                                # await self.page.waitForSelector('span.fullscreen-toggle')
                                await asyncio.sleep(1)  # TODO: replace with current channel detection
                            else:
                                logger.info(f"Could not set channel '{channel}'")
                        else:
                            logger.info(f"'{channel}' is already the current channel")
                        break
                    self._start_heartbeat()
                else:
                    logger.info(f"Could not set channel '{channel}' in state {self.state}")
            except Exception:
                logger.exception('Exception in change_channel')
                await self.dump_page('clicking')

    async def dump_page(self, mode):
        try:
            t = datetime.now().isoformat(sep='_', timespec='seconds')
            with open(f'page_dump_{t}_foxtel_{mode}.html', 'w') as f:
                f.write(await self.page.content())
        except:
            logger.exception('dump failed')

    async def _change_page(self, new_state):
        current_state = self.state
        logger.info(f"Change state from {current_state} to {new_state}")
        if current_state != new_state:
            try:
                await self._stop_heartbeat()
                if not await self._check_connection():
                    current_state = self.state
                    logger.info(f"Post restart Change state from {current_state} to {new_state}")
                next_state = self.next_state[new_state]
                if current_state in next_state:
                    handlers = next_state[current_state]
                    if isinstance(handlers, list):
                        for handler in handlers:
                            await handler()
                            await self._update_state()
                    else:
                        handler = handlers
                        await handler()
                        await self._update_state()
                    await self.show_timeouts()
                if self.state != new_state:
                    logger.info(f"Could not transition from {current_state} to {new_state} is {self.state}")
                    await self.dump_page('1')
                    # await asyncio.sleep(1)
                    return False
            except RuntimeError:
                await self.dump_page('re')
                logger.exception(f"RuntimeError could not transition from {current_state} to {new_state}")
                # await asyncio.sleep(1)
                return False
            except Exception:
                logger.exception(f"Exception could not transition from {current_state} to {new_state}")
                await self.dump_page('ex')
            self._start_heartbeat()
        return True

    async def change_page(self, new_state):
        async with self._lock:
            await self._change_page(new_state)

    async def stop(self):
        logger.info('foxtel stop')
        await self._stop_heartbeat()
        await self._stop_reload_timer()
        if self.browser:
            logger.info('foxtel close browser')
            await self.browser.close()
            logger.info('foxtel close browser done')
        self.browser = None
        self.page = None
