import usocket as socket
import ubinascii as binascii
import urandom as random
import ure as re
import ustruct as struct
import urandom as random
import usocket as socket
from ucollections import namedtuple

OP_CONT = const(0x0)
OP_TEXT = const(0x1)
OP_BYTES = const(0x2)
OP_CLOSE = const(0x8)
OP_PING = const(0x9)
OP_PONG = const(0xa)

CLOSE_OK = const(1000)
CLOSE_GOING_AWAY = const(1001)
CLOSE_PROTOCOL_ERROR = const(1002)
CLOSE_DATA_NOT_SUPPORTED = const(1003)
CLOSE_BAD_DATA = const(1007)
CLOSE_POLICY_VIOLATION = const(1008)
CLOSE_TOO_BIG = const(1009)
CLOSE_MISSING_EXTN = const(1010)
CLOSE_BAD_CONDITION = const(1011)


URL_RE = re.compile(r'ws://([A-Za-z0-9\-\.]+)(?:\:([0-9]+))?(/.+)?')
URI = namedtuple('URI', ('hostname', 'port', 'path'))

def urlparse(uri):
    match = URL_RE.match(uri)
    if match:
        return URI(match.group(1), int(match.group(2)), match.group(3))

class Websocket:

    def __init__(self, sock,cli=False):
        self._sock = sock
        self.open = True
        self.is_client = cli

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def settimeout(self, timeout):
        self._sock.settimeout(int(timeout))

    def read_frame(self, max_size=None):
        byte1, byte2 = struct.unpack('!BB', self._sock.read(2))

        fin = bool(byte1 & 0x80)
        opcode = byte1 & 0x0f

        mask = bool(byte2 & (1 << 7))
        length = byte2 & 0x7f

        if length == 126:
            length, = struct.unpack('!H', self._sock.read(2))
        elif length == 127:
            length, = struct.unpack('!Q', self._sock.read(8))

        if mask:
            mask_bits = self._sock.read(4)

        try:
            data = self._sock.read(length)
        except MemoryError:
            self.close(code=CLOSE_TOO_BIG)
            return True, OP_CLOSE, None

        if mask:
            data = bytes(b ^ mask_bits[i % 4]
                         for i, b in enumerate(data))

        return fin, opcode, data

    def write_frame(self, opcode, data=b''):
        fin = True
        mask = self.is_client  # messages sent by client are masked

        length = len(data)

        byte1 = 0x80 if fin else 0
        byte1 |= opcode

        byte2 = 0x80 if mask else 0

        if length < 126:
            byte2 |= length
            self._sock.write(struct.pack('!BB', byte1, byte2))

        elif length < (1 << 16):  # Length fits in 2-bytes
            byte2 |= 126
            self._sock.write(struct.pack('!BBH', byte1, byte2, length))

        elif length < (1 << 64):
            byte2 |= 127
            self._sock.write(struct.pack('!BBQ', byte1, byte2, length))

        else:
            raise ValueError()

        if mask:
            mask_bits = struct.pack('!I', random.getrandbits(32))
            self._sock.write(mask_bits)

            data = bytes(b ^ mask_bits[i % 4]
                         for i, b in enumerate(data))

        self._sock.write(data)

    def recv(self):
        assert self.open

        while self.open:
            try:
                fin, opcode, data = self.read_frame()
            except ValueError:
                self._close()
                return

            if not fin:
                raise NotImplementedError()

            if opcode == OP_TEXT:
                return data.decode('utf-8')
            elif opcode == OP_BYTES:
                return data
            elif opcode == OP_CLOSE:
                self._close()
                return
            elif opcode == OP_PONG:
                # Ignore this frame, keep waiting for a data frame
                continue
            elif opcode == OP_PING:
                self.write_frame(OP_PONG, data)
                continue
            elif opcode == OP_CONT:
                # This is a continuation of a previous frame
                raise NotImplementedError(opcode)
            else:
                raise ValueError(opcode)

    def send(self, buf):
        assert self.open

        if isinstance(buf, str):
            opcode = OP_TEXT
            buf = buf.encode('utf-8')
        elif isinstance(buf, bytes):
            opcode = OP_BYTES
        else:
            raise TypeError()

        self.write_frame(opcode, buf)

    def close(self, code=CLOSE_OK, reason=''):
        if not self.open:
            return

        buf = struct.pack('!H', code) + reason.encode('utf-8')

        self.write_frame(OP_CLOSE, buf)
        self._close()

    def _close(self):
        self.open = False
        self._sock.close()


class client:
    @classmethod
    def connect(cls,uri):
        uri = urlparse(uri)
        assert uri

        sock = socket.socket()
        addr = socket.getaddrinfo(uri.hostname, uri.port)
        sock.connect(addr[0][4])

        def send_header(header, *args):
            sock.send(header % args + '\r\n')

        key = binascii.b2a_base64(bytes(random.getrandbits(8)
                                        for _ in range(16)))[:-1]

        send_header(b'GET %s HTTP/1.1', uri.path or '/')
        send_header(b'Host: %s:%s', uri.hostname, uri.port)
        send_header(b'Connection: Upgrade')
        send_header(b'Upgrade: websocket')
        send_header(b'Sec-WebSocket-Key: %s', key)
        send_header(b'Sec-WebSocket-Version: 13')
        send_header(b'Origin: http://localhost')
        send_header(b'')

        header = sock.readline()[:-2]
        assert header == b'HTTP/1.1 101 Switching Protocols', header

        while header:
            header = sock.readline()[:-2]

        return Websocket(sock,True)
