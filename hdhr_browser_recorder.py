#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
# import os
import pprint
import asyncio

from configobj import ConfigObj

from quart import Quart, abort, jsonify, render_template_string

from support.xvfb import XvfbAsync
from support.x11vnc import X11vncAsync
from support.timer import Timer
from support import proxyControl as hdhomerun_control
# from support.proxyControl import HDHomeRunUdpServer, HDHomeRunTcpServer, hdhomerun_validate_device_id
from urllib.parse import quote, unquote
import hypercorn
# from contextlib import suppress
import logging
from logging import handlers


config = ConfigObj('hdhr_browser_recorder.cfg')


class DispatchingFormatter:

    def __init__(self, formatters, default_formatter):
        self._formatters = formatters
        self._default_formatter = default_formatter

    def format(self, record):
        formatter = self._formatters.get(record.name, self._default_formatter)
        return formatter.format(record)


_log_handler = logging.StreamHandler()
_fmt = '[{asctime}:{levelname[0]}:{name}] {message}'
_formatter = DispatchingFormatter({
    'quart.serving': logging.Formatter('[%(asctime)s] %(message)s')
    },
    logging.Formatter(_fmt, style='{'))
_log_handler.setFormatter(_formatter)
_log_handler.setLevel(logging.INFO)

_file_log_handler = handlers.TimedRotatingFileHandler('hdhr_browser_recorder.log', when='MIDNIGHT', backupCount=10)
_file_log_handler.setFormatter(_formatter)
_file_log_handler.setLevel(logging.INFO)

root_logger = logging.getLogger('')
root_logger.setLevel(logging.INFO)
root_logger.addHandler(_log_handler)
root_logger.addHandler(_file_log_handler)
logger = logging.getLogger('hdhr_browser_recorder')

provider_service = None
provider_guide = None

app = Quart(__name__)
app.provider_service = None
app.provider_guide = None
app.stopping = None
app.udp_server = None
app.tcp_server = None


def configure_service():
    global provider_guide
    global provider_service

    if not config:
        logger.error('config file not found')
        sys.exit(2)
    if config['provider'] == 'foxtelgo':
        from providers.foxtelgo.foxtel_service import FoxtelService
        from providers.foxtelgo import foxtel_guide
        provider_service = FoxtelService
        provider_guide = foxtel_guide
        return 0
    logger.error('Invalid provider {} configured'.format(config['provider']))
    sys.exit(1)


async def _get_channels():
    global provider_guide
    global app
    dump_data = False
    channels = await app.provider_service.get_channels()
    channels_aux = await provider_guide.get_channel_map()
    new_channels = []
    for channel in channels:
        try:
            c = channels_aux[provider_guide.remap_channel_name(channel)]
            if 'sd_number' in c:
                number = c['sd_number']
            else:
                number = c['number']
            entry = {
                'name': channel,
                'number': number
            }
            new_channels.append(entry)
        except KeyError:
            logger.info(f"number for channel '{channel}' not found")
            dump_data = True
    if dump_data:
        pprint.pprint(channels)
        pprint.pprint(channels_aux)

    return new_channels


async def main_async(coro):
    xvfb = None
    x11vnc = None
    task = None
    try:
        xvfb = XvfbAsync(option_list=[
            '-ac',
            '-extension', "RANDR",
            '-extension', "RENDER",
            '-extension', "GLX"],
            width=1280, height=720, colordepth=24)
        await xvfb.start()
        x11vnc = X11vncAsync(xvfb.new_display)
        task = asyncio.create_task(x11vnc.start())

        logger.info("display :%s" % xvfb.new_display)
        await coro()
    finally:
        if x11vnc:
            await x11vnc.stop()
        if task:
            await task
        if xvfb:
            await xvfb.stop()

    return 0


###################################################################################
#  HDHR Server
###################################################################################

# URL format: <protocol>://<username>:<password>@<hostname>:<port>, example: https://test:1234@localhost:9981
class Config:
    restfulURL = 'http://VDR:8002'
    streamdevURL = 'http://VDR:3000/EXT'
    proxyHostAddr = '192.168.1.1'
    proxyBindAddr = '0.0.0.0'
    proxyPort = 5004  # do _NOT_ change this.
    proxyURL = 'http://%s:%s' % (proxyHostAddr, proxyPort)
    tunerCount = 1    # number of tuners in vdr


discover_data = {
    'FriendlyName': 'foxtelgoProxy',
    'Manufacturer': 'Silicondust',
    'ModelNumber': 'HDTC-2US',
    'FirmwareName': 'hdhomeruntc_atsc',
    'TunerCount': Config.tunerCount,
    # 'FirmwareVersion': '20150826',
    'FirmwareVersion': '20190410',
    'DeviceID': '12345687',
    'DeviceAuth': 'test1234',
    'BaseURL': Config.proxyURL,
    'LineupURL': '%s/lineup.json' % Config.proxyURL,
}


app.config.update({
    'DEBUG': True,
})


@app.route('/discover.json')
async def discover():
    logger.info("discover")
    return jsonify(discover_data)


@app.route('/lineup_status.json')
async def status():
    logger.info("status")
    return jsonify({
        'ScanInProgress': 0,
        'ScanPossible': 1,
        'Source': "Cable",
        'SourceList': [
            'Cable',
            # 'Antenna',
        ]
    })


@app.route('/lineup.json')
async def get_lineup():
    lineup = []

    channels = await _get_channels()
    for c in channels:
        url = '%s/auto/%s' % (Config.proxyURL, quote(c['name'], safe=''))
        lineup.append({'GuideNumber': str(c['number']),
                       'GuideName': c['name'],
                       'URL': url
                       })

    return jsonify(lineup)


@app.route('/lineup.post', methods=['GET', 'POST'])
async def lineup_post():
    return ''


async def _cancel_stop():
    if app.stopping is not None:
        await app.stopping.cancel()
    app.stopping = None


@app.route('/auto/<channel>')
async def stream(channel: str):
    await _cancel_stop()
    real_channel = unquote(channel)
    logger.info(f"channel is {real_channel}")
    abort(404)


def shutdown(loop):
    if loop:
        logger.info("Stopping event loop ...")
        loop.stop()


@app.before_serving
async def create_services():
    global provider_service
    # noinspection PyBroadException
    # loop = asyncio.get_event_loop()
    # for signame in ('SIGINT','SIGTERM'):
    #    loop.add_signal_handler(getattr(signal, signame), functools.partial(shutdown, loop))
    logger.info('Create services')
    # remove custom logger for quart.serving
    quart_logger = logging.getLogger('quart.serving')
    while quart_logger.handlers:
        quart_logger.removeHandler(quart_logger.handlers[0])

    try:
        if app.provider_service is None:
            app.provider_service = provider_service()
        hdhomerun_control.set_config(discover_data)
        if app.udp_server is None:
            # app.udp_server = hdhomerun_control.HDHomeRunUdpServer('192.168.1.255')
            app.udp_server = hdhomerun_control.HDHomeRunUdpServer('127.255.255.255')
        if app.tcp_server is None:
            # app.tcp_server = hdhomerun_control.HDHomeRunUdpServer('192.168.1.1')
            app.tcp_server = hdhomerun_control.HDHomeRunTcpServer('127.0.0.1')
    except Exception:
        logger.info('Create services exception', exc_info=1)
        # traceback.print_exc(file=sys.stdout)


@app.after_serving
async def destroy_services():
    await _cancel_stop()
    if app.provider_service is not None:
        await app.provider_service.stop()
        app.provider_service = None
    if app.udp_server is not None:
        await app.udp_server.stop()
        app.udp_server = None
    if app.tcp_server is not None:
        await app.tcp_server.stop()
        app.tcp_server = None


@app.route('/record', defaults={'channel': '', 'duration': 0.0})
@app.route('/record/<channel>', defaults={'duration': 0.0})
@app.route('/record/<channel>/<float:duration>')
async def start_recording_timed(channel: str, duration: float):
    real_channel = unquote(channel)
    await _cancel_stop()
    await app.provider_service.process_event(provider_service.Event.StartRecord, real_channel)
    if duration > 0.0:
        app.stopping = Timer(float(duration) + 30.0,
                             app.provider_service.process_event(provider_service.Event.StopPlay))
    return jsonify({
        'result': 'OK'
    })


@app.route('/play', defaults={'channel': ''})
@app.route('/play/<channel>')
async def start_playing(channel: str):
    await _cancel_stop()
    real_channel = unquote(channel)
    await app.provider_service.process_event(provider_service.Event.StartPlay, real_channel)
    return jsonify({
        'result': 'OK'
    })


@app.route('/stop', defaults={'delay': 0.0})
@app.route('/stop/<float:delay>')
async def stop(delay: float):
    await _cancel_stop()
    action = app.provider_service.process_event(provider_service.Event.StopPlay)
    if delay > 0.0:
        app.stopping = Timer(float(delay), action)
    else:
        await action
    return jsonify({
        'result': 'OK'
    })


@app.route('/off', defaults={'delay': 0.0})
@app.route('/off/<float:delay>')
async def turn_off(delay: float):
    await _cancel_stop()
    action = app.provider_service.process_event(provider_service.Event.Stop)
    if delay > 0.0:
        app.stopping = Timer(float(delay), action)
    else:
        await action
    return jsonify({
        'result': 'OK'
    })


@app.route('/reload')
async def reload():
    await app.provider_service.process_event(provider_service.Event.Reload)
    return jsonify({
        'result': 'OK'
    })


@app.route('/restart')
async def restart():
    await app.provider_service.process_event(provider_service.Event.Restart)
    return jsonify({
        'result': 'OK'
    })


@app.route('/dump/<cmd>')
async def dump(cmd):
    if app.provider_service._foxtel is not None:
        await app.provider_service._foxtel.dump_page(cmd)
    return jsonify({
        'result': 'OK'
    })


device_xml = '''
<root xmlns="urn:schemas-upnp-org:device-1-0">
    <specVersion>
        <major>1</major>
        <minor>0</minor>
    </specVersion>
    <URLBase>{{ data.BaseURL }}</URLBase>
    <device>
        <deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>
        <friendlyName>{{ data.FriendlyName }}</friendlyName>
        <manufacturer>{{ data.Manufacturer }}</manufacturer>
        <modelName>{{ data.ModelNumber }}</modelName>
        <modelNumber>{{ data.ModelNumber }}</modelNumber>
        <serialNumber></serialNumber>
        <UDN>uuid:{{ data.DeviceID }}</UDN>
    </device>
</root>
'''


@app.route('/')
@app.route('/device.xml')
async def device():
    return await render_template_string(device_xml, data=discover_data), {'Content-Type': 'application/xml'}


async def timer_test():
    async def callback():    # noinspection PyBroadException

        logger.info("callback")

    timer1 = Timer(5, callback())
    timer2 = Timer(10, callback())
    await asyncio.sleep(7)
    await timer2.cancel()
    await timer1.cancel()   # ok


@app.cli.command('test')
def test():
    # asyncio.run(main_async())
    # asyncio.run(timer_test())
    pass


# @app.cli.command('start')
# def start():0x12345674
#     # asyncio.create_task(run_recorder)
#     pass
#
#
# @app.cli.command('stop')
# def stop():
#     pass
#
#
# @app.cli.command('channels')
# def channels():
#     print("channels")
#     asyncio.run(main_async(lineup))
#     return 0

@app.cli.command('deviceid')
def check_device_id():
    # id = 0x12345670
    id = 12345678
    for i in range(16):
        if hdhomerun_control.hdhomerun_validate_device_id(id + i):
            print("good = 0x%08x (%d)" % (id + i, id + i))
#           12345687 = 0x00bc6157
#           0x12345674


@app.cli.command('run')
def main():
    logger.info('**** Starting server ****')
    # noinspection PyUnresolvedReferences
    try:
        app.run(host=Config.proxyBindAddr, port=Config.proxyPort)
    except hypercorn.utils.LifespanTimeout:
        logger.info("LifespanTimeout Shutdown occurred")

    return 0


if __name__ == '__main__':
    configure_service()
    sys.exit(app.cli.main())
