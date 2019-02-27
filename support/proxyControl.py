from io import BytesIO
import os
import socket
import struct
import asyncio
from contextlib import suppress
from . import crc32c
import logging


logger = logging.getLogger(__name__)


HDHOMERUN_DISCOVER_UDP_PORT = 65001
HDHOMERUN_CONTROL_TCP_PORT = 65001
HDHOMERUN_MAX_PACKET_SIZE = 1460
HDHOMERUN_MAX_PAYLOAD_SIZE = 1452

HDHOMERUN_TYPE_DISCOVER_REQ = 0x0002
HDHOMERUN_TYPE_DISCOVER_RPY = 0x0003
HDHOMERUN_TYPE_GETSET_REQ = 0x0004
HDHOMERUN_TYPE_GETSET_RPY = 0x0005
HDHOMERUN_TYPE_UPGRADE_REQ = 0x0006
HDHOMERUN_TYPE_UPGRADE_RPY = 0x0007

HDHOMERUN_TAG_DEVICE_TYPE = 0x01
HDHOMERUN_TAG_DEVICE_ID = 0x02
HDHOMERUN_TAG_GETSET_NAME = 0x03
HDHOMERUN_TAG_GETSET_VALUE = 0x04
HDHOMERUN_TAG_GETSET_LOCKKEY = 0x15
HDHOMERUN_TAG_ERROR_MESSAGE = 0x05
HDHOMERUN_TAG_TUNER_COUNT = 0x10
HDHOMERUN_TAG_DEVICE_AUTH_BIN = 0x29
HDHOMERUN_TAG_BASE_URL = 0x2A
HDHOMERUN_TAG_DEVICE_AUTH_STR = 0x2B

HDHOMERUN_DEVICE_TYPE_WILDCARD = 0xFFFFFFFF
HDHOMERUN_DEVICE_TYPE_TUNER = 0x00000001
HDHOMERUN_DEVICE_ID_WILDCARD = 0xFFFFFFFF

verbose = 0


config = {
    'FriendlyName': 'HDHRBrowserRecorderProxy',
    'Manufacturer': 'Silicondust',
    'ModelNumber': 'HDTC-2USA',
    'FirmwareName': 'hdhomeruntc_atsc',
    'TunerCount': 1,
    'FirmwareVersion': '20190410',
    'DeviceID': '12345687',
    'DeviceAuth': 'test1234',
    'BaseURL': '',
    'LineupURL': '',
}

info = {
    '/tuner0/lockkey': 'none',
    '/tuner0/channelmap': 'us-cable',
    '/tuner0/target': 'udp://127.0.0.1:55555',
    '/tuner0/channel': 'none',
}


def get_set(d, k, v, lockkey):
    if v is not None:
        d[k] = v
    else:
        v = d[k]
    return [v]


def get_only(d, k):
    return d[k]


def get_tuner_status(tuner):
    # 'ch=qam:33 lock=qam256 ss=83 snq=90 seq=100 bps=38807712 pps=0'
    channel_info = info[f'/tuner{tuner}/channel']
    logger.info(f'Channel {channel_info} status')
    if info[f'/tuner{tuner}/channel'] != 'none':
        mod, channel = channel_info.split(':')
        mod = 'qam'
        return f'ch={mod}:{channel} lock={mod} ss=83 snq=90 seq=100 bps=38807712 pps=0'
    return f'ch=none lock=none ss=0 snq=0 seq=0 bps=0 pps=0'


def get_tuner_streaminfo(tuner):
    channel_info = info[f'/tuner{tuner}/channel']
    logger.info(f'Channel {channel_info} status')
    if info[f'/tuner{tuner}/channel'] != 'none':
        mod, channel = channel_info.split(':')
        channel = (int(channel)//100000 - 450) // 60
        return f"{channel}: {channel} My Channel\n"
    return None


get_set_values = {
    '/sys/model': lambda v, lk: get_only(config, 'ModelNumber'),
    '/tuner0/channelmap': lambda v, lk: get_only(info, '/tuner0/channelmap'),
    '/tuner0/lockkey': lambda v, lk: get_set(info, '/tuner0/lockkey', v, lk),
    '/tuner0/target': lambda v, lk: get_set(info, '/tuner0/target', v, lk),
    '/tuner0/channel': lambda v, lk: get_set(info, '/tuner0/channel', v, lk),
    '/tuner0/status': lambda v, lk: get_tuner_status(0),
    '/tuner0/streaminfo': lambda v, lk: get_tuner_streaminfo(0),
}
get_set_values['help'] = lambda v: [x for x in get_set_values.keys()]


def set_config(new_config):
    global config
    config = new_config


def hdhomerun_validate_device_id(device_id: int) -> bool:
    lookup_table = [0xA, 0x5, 0xF, 0x6, 0x7, 0xC, 0x1, 0xB, 0x9, 0x2, 0x8, 0xD, 0x4, 0x3, 0xE, 0x0]

    checksum = 0

    checksum ^= lookup_table[(device_id >> 28) & 0x0F]
    checksum ^= (device_id >> 24) & 0x0F
    checksum ^= lookup_table[(device_id >> 20) & 0x0F]
    checksum ^= (device_id >> 16) & 0x0F
    checksum ^= lookup_table[(device_id >> 12) & 0x0F]
    checksum ^= (device_id >> 8) & 0x0F
    checksum ^= lookup_table[(device_id >> 4) & 0x0F]
    checksum ^= (device_id >> 0) & 0x0F

    return checksum == 0


def retrieve_type_and_payload(packet):
    header = packet[:4]
    checksum = packet[-4:]
    payload = packet[4:-4]

    packet_type, payload_length = struct.unpack('>HH', header)

    if payload_length != len(payload):
        logger.info('Bad packet payload length')
        return False

    if checksum != struct.pack('>I', crc32c.cksum(header + payload)):
        logger.info('Bad checksum')
        return False

    return packet_type, payload


def create_packet(packet_type, payload):
    header = struct.pack('>HH', packet_type, len(payload))
    data = header + payload
    checksum = crc32c.cksum(data)
    packet = data + struct.pack('>I', checksum)

    return packet


def process_packet(packet, client, log_prefix=''):
    packet_type, request_payload = retrieve_type_and_payload(packet)

    logger.info(log_prefix + f'Processing Packet {packet_type}')
    if packet_type == HDHOMERUN_TYPE_DISCOVER_REQ:
        logger.info(log_prefix + 'Discovery request received from ' + client[0])
        # Device Type Filter (tuner)
        response_payload = struct.pack('>BBI', HDHOMERUN_TAG_DEVICE_TYPE, 0x04, HDHOMERUN_DEVICE_TYPE_TUNER)
        # Device ID Filter (any)
        response_payload += struct.pack('>BBI', HDHOMERUN_TAG_DEVICE_ID, 0x04, int(config['DeviceID'], 10))
        # Device ID Filter (any)
        response_payload += struct.pack('>BB{0}s'.format(len(config['BaseURL'])), HDHOMERUN_TAG_GETSET_NAME,
                                        len(config['BaseURL'].encode('utf-8')), config['BaseURL'].encode('utf-8'))
        response_payload += struct.pack('>BB{0}s'.format(len(config['BaseURL'])), HDHOMERUN_TAG_BASE_URL,
                                        len(config['BaseURL'].encode('utf-8')), config['BaseURL'].encode('utf-8'))
        # Device ID Filter (any)
        response_payload += struct.pack('>BBB', HDHOMERUN_TAG_TUNER_COUNT, 0x01, config['TunerCount'])

        return create_packet(HDHOMERUN_TYPE_DISCOVER_RPY, response_payload)

    # TODO: Implement request types
    if packet_type == HDHOMERUN_TYPE_GETSET_REQ:
        logger.info(log_prefix + 'Get set request received from ' + client[0])
        get_set_name = None
        get_set_value = None
        payload_io = BytesIO(request_payload)
        lockkey = ''
        while True:
            header = payload_io.read(2)
            if not header:
                break

            tag, length = struct.unpack('>BB', header)
            if length > 127:
                header_extra = payload_io.read(1)
                length_msb, = struct.unpack('>B', header_extra)
                if length_msb > 127:
                    logger.info(log_prefix + 'Unable to determine tag length, the correct way to determine '
                                       'a length larger than 127 must still be implemented.')
                    return False
                length = (length & 127) + (length_msb << 7)

            logger.info(f'Tag {tag}')
            # TODO: Implement other tags
            if tag == HDHOMERUN_TAG_GETSET_NAME:
                get_set_name, zero = struct.unpack('>{0}sB'.format(length - 1), payload_io.read(length))
            elif tag == HDHOMERUN_TAG_GETSET_VALUE:
                get_set_value, zero = struct.unpack('>{0}sB'.format(length - 1), payload_io.read(length))
            elif tag == HDHOMERUN_TAG_GETSET_LOCKKEY:
                # set lockkey
                lockkey, = struct.unpack('>I'.format(length), payload_io.read(length))
                logger.info(f'lockkey {lockkey}')
            else:
                logger.warning(f'Unknown tag {tag} length {length}')
                p = struct.unpack('>{0}s'.format(length), payload_io.read(length))
                logger.info(f'  data {p}')
                continue
            logger.info(f'Name {get_set_name} Value {get_set_value}')

        if get_set_name is None:
            return False
        else:
            name = get_set_name.decode('utf-8')
            logger.info(f'Name is {name}')
            if name in get_set_values:
                item = get_set_values[name]
                if get_set_value is None:
                        if callable(item):
                            get_set_value = item(None, None)
                        else:
                            get_set_value = item
                        if get_set_value is not None:
                            if not isinstance(get_set_value, list):
                                get_set_value = [get_set_value]
                            try:
                                get_set_value_orig = get_set_value
                                get_set_value = [x.encode('utf-8') for x in get_set_value_orig]
                            except AttributeError:
                                logger.exception(f'bad data {get_set_value_orig}')
                else:
                    # is a set
                    if callable(item):
                        # TODO pass lockkey
                        item(get_set_value.decode('utf-8'), lockkey)

            if not isinstance(get_set_value, list):
                get_set_value = [get_set_value]

            # response_payload = struct.pack('>BB{0}sB'.format(len(get_set_name)), HDHOMERUN_TAG_GETSET_NAME,
            #                                len(get_set_name) + 1, get_set_name, 0)
            response_payload = b''

            if get_set_value is not None and None not in get_set_value:
                logger.info(f'Value is {get_set_value}')
                for x in get_set_value:
                    response_payload += struct.pack('>BB{0}sB'.format(len(x)), HDHOMERUN_TAG_GETSET_VALUE,
                                                    len(x) + 1, x, 0)

            return create_packet(HDHOMERUN_TYPE_GETSET_RPY, response_payload)

    logger.info(log_prefix + 'Unhandled request %02x received from %s' % (packet_type, client[0]))

    return False


class HDHomeRunTcpServerProtocol(asyncio.Protocol):
    def __init__(self, *cwargs, **kwargs):
        super().__init__(*cwargs, **kwargs)
        self.log_prefix = 'TCP Server - '

    def connection_made(self, transport):
        self.peername = transport.get_extra_info('peername')
        logger.info(self.log_prefix + 'Connection from {}'.format(self.peername))
        self.transport = transport

    def data_received(self, data):
        response_packet = process_packet(data, self.peername)
        if response_packet:
            logger.info(self.log_prefix + f'Sending TCP reply over TCP to {self.peername}')
            self.transport.write(response_packet)
        else:
            logger.info(self.log_prefix + 'No valid TCP request received, nothing to send to client')

        logger.info(self.log_prefix + 'Close the client socket')
        self.transport.close()


class HDHomeRunUdpProtocol(asyncio.DatagramProtocol):

    def __init__(self, loop):
        super().__init__()
        self.transport = None
        self.loop = loop
        self.log_prefix = 'UDP Server - '
        self.on_connection_lost = loop.create_future()

    def connection_made(self, transport):
        # logger.info('connected')
        self.transport = transport

    def connection_lost(self, ex):
        if ex is not None:
            self.transport.close()
        self.on_connection_lost.set_result(True)

    def datagram_received(self, data, addr):
        response_packet = process_packet(data, addr)
        if response_packet:
            logger.info(self.log_prefix + f'Sending UDP reply over udp to {addr}')
            self.transport.sendto(response_packet, addr)
        else:
            logger.info(self.log_prefix + 'No discovery request received, nothing to send to client')


class HDHomeRunTcpServer:
    def __init__(self, bind_addr='192.168.1.1', bind_port=HDHOMERUN_DISCOVER_UDP_PORT):
        self._task = asyncio.create_task(self._serve(bind_addr, bind_port))
        self._transport = None
        self._protocol = None
        self._server = None

    async def _serve(self, bind_addr, bind_port):
        loop = asyncio.get_running_loop()

        try:
            server = await loop.create_server(
                lambda: HDHomeRunTcpServerProtocol(),
                bind_addr, bind_port)

            logger.info(f'HDHR TCP Server listening on {bind_addr, bind_port}')
            async with server:
                await server.serve_forever()
        except asyncio.CancelledError:
            logger.info('HDHR TCP Server cancelled')
        logger.info('HDHR TCP Server closed')

    async def stop(self):
        # logger.info('tcp stop 1')
        # self._transport.close()
        self._task.cancel()
        # logger.info('tcp stop 2')
        await self._task
        # logger.info('tcp stop 3')
        self._task = None


class HDHomeRunUdpServer:
    def __init__(self, bind_addr='192.168.1.1', bind_port=HDHOMERUN_DISCOVER_UDP_PORT):
        self._task = asyncio.create_task(self._serve(bind_addr, bind_port))
        self._transport = None
        self._protocol = None
        self._server = None

    async def _serve(self, bind_addr, bind_port):
        loop = asyncio.get_running_loop()
        # logger.info('_serve')
        is_broadcast = True  # bind_addr.endswith('.255')
        try:
            self._server = loop.create_datagram_endpoint(lambda _loop=loop: HDHomeRunUdpProtocol(_loop),
                                                         local_addr=(bind_addr, bind_port),
                                                         allow_broadcast=is_broadcast)
            self._transport, self._protocol = await self._server
            # logger.info('_serve create done')
            sock_addr, sock_port = self._transport.get_extra_info("sockname")
            logger.info(f'HDHR UDP Server listening on {sock_addr, sock_port}')
            await self._protocol.on_connection_lost
        except asyncio.CancelledError:
            logger.info('HDHR UDP Server cancelled')
        logger.info('HDHR UDP Server closed')

    async def stop(self):
        # logger.info('udp stop 1')
        self._transport.close()
        # logger.info('udp stop 2')
        await self._task
        # logger.info('udp stop 3')
        self._task = None


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port_type')
    parser.add_argument('--verbose', type=int, default=0)
    args = parser.parse_args()
    verbose = args.verbose

    try:
        if args.port_type == 'tcp':
            tcp_server()
        else:
            udp_server()
    except KeyboardInterrupt:
        exit(0)
