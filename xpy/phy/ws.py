if UPY:
    import struct
    import usocket as socket
    import ubluelet as bluelet
    import ujson as json

    from uhashlib import sha1
    from ubinascii import b2a_base64 as b64encode
    from struct import unpack,calcsize

    import gc

else:
    import struct
    import socket
    import json
    from hashlib import sha1
    from binascii import b2a_base64 as b64encode
    from struct import unpack,calcsize


import websocket

global sock
global serving


blocking=True

EAGAIN = OSError(11)

FIN    = 0x80
OPCODE = 0x0f
MASKED = 0x80
PAYLOAD_LEN = 0x7f
PAYLOAD_LEN_EXT16 = 0x7e
PAYLOAD_LEN_EXT64 = 0x7f

OPCODE_TEXT = 0x01
CLOSE_CONN  = 0x8


def handshake(client):
    print("<handshake>")
    header=b""
    while header.find(b'\r\n\r\n') == -1:
        header += client.recv(16)
        if header.startswith(b'MTU='):
            return header.decode('utf8')

    lines = header.split(b"\r\n")
    d=dict()
    for line in lines[1:]:
        if not line :continue
        header,value = line.split(b": ",1)
        d[header]=value

    # compute Response Key
    GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    hash = sha1( d[b'Sec-WebSocket-Key'] + GUID)
    d=hash.digest()
    response_key = b64encode(d).strip().decode('ASCII')
    template='HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n\r\n'
    handshake=template%response_key
    client.send(handshake.encode())
    print("</handshake>")

    return 'ws'


import atm_cell




#SLEEP = .0005

def rsv_pad(data,sz):
    if len(data)<sz-2:
        return b''.join( (b'#', data , b' '*( (sz-2) - len(data))  , b'\x00', ) )
    return b''.join( (b'#', data , b'#'*( (sz-1) - len(data)), ) )


class PHY_Network_WS(atm_cell.TXRX):
    #max ws tx
    WS_MTU = 125

    RX_MTU = 1492
    TX_MTU = 125

    def __init__(self,port,addr="0.0.0.0",mtu=None):
        global sock
        self.port = int(port)
        self.client = None
        self.serving=True
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        ai = socket.getaddrinfo(addr, port)
        addr = ai[0][4]
        sock.bind(addr)

        sock.listen(.002)
        sock.setblocking(blocking)
        self.fifo = []
        self.q = []
        self.Wake = atm_cell.Lapse( SLEEP )
        if mtu:
            self.RX_MTU = mtu


    def start(self):
        global sock
        print("<Thread Serving at", self.port,'>')
        while self.serving:
            self.client = None
            try:
                self.client, self.address = sock.accept()
            except Exception as e:
                if e.args[0]==11:
                    continue
                else:
                    print("159:",e)

            ct =  handshake(self.client)

            print("client connected ",self.address,end=' using ')

            if ct =='ws':
                mtu = self.RX_MTU
                print('websocket MTU=%s' % mtu)
            else:
                mtu = int( ct.split('=',1)[-1] )
                ct = 'std'
                print('socket MTU=%s' % SI(mtu) )
            break

        self.setup(self.client,True)
        print("</Thread Serving>")
        return ct,mtu


    def RX_ws(self):
        return self.ws.read()

    def TX_ws(self,payload):
        if not payload:
            return

        if not isinstance(payload,bytes):
            payload = payload.encode('UTF-8')

        if self.stat:
            self.stx += len(payload)

        n = self.TX_MTU-2
        for i in range(0, len(payload), n):
            try:
                self.ws.write( rsv_pad( payload[i:i+n] , self.TX_MTU ) )
            except:
                print('149: broken link')
                return

    def TX_std(self,data):
        if not isinstance(data,bytes):
            data = bytes(data,'UTF-8')
        if self.stat:
            self.stx +=len(data)
        return self.sock.send( rsv_pad(data, self.TX_MTU) )

    def RX_std(self):
        return self.sock.recv(self.RX_MTU)

    def flush(self):pass


    def switch(self,ct, mtu_rx , mtu_tx=125):
        self.client.setblocking(False)
        if ct=='ws':
            self.ws = websocket.websocket(self.client, True)
            if mtu_tx>self.WS_MTU:
                print("180: not using user MTU [%s] because rsv not implemented and mode is websocket" % mtu_rx)

            self.RX = self.RX_ws
            self.TX = self.TX_ws
            #max receive
            self.RX_MTU = mtu_rx
        else:
            print('205: standard socket, mtu=',mtu_rx)
            self.RX = self.RX_std
            self.TX = self.TX_std
            #max receive
            self.RX_MTU = mtu_rx
            #but limit send
            mtu = mtu_tx

        self.TX_MTU = mtu_tx
        self.BO = self.RX_MTU * 4

        self.errcnt = 0
        self.log = []


    def step(self):
        try:
            data= self.RX()
        except OSError:
            return EAGAIN

        if data is None:
            return EAGAIN

        ld = len(data)
        self.fifo.append( data )

        data  = b''.join( self.fifo )

        if len(data) > self.BO:
            warn('212: buffer overflow %s > %s' % (len(data) , self.BO ) )
            data = b''.join( (data.strip() , b'\x00' ) )

        self.fifo = data.split( b'\x00',1)


        if len(self.fifo)>1:
            data = self.fifo.pop(0).strip()

            if not len(data):
                #continue
                return

            if self.stat:
                self.srx += len(data)


            if data[0]!=35: #b'#':
                print('data=',len(data),data)
                print('q=',self.fifo)
                #continue
                return

            try:
                self.q.append(  json.loads(data[1:].strip())  )
            except Exception as e:
                e = repr( e)

                if not e in self.log:
                    self.log.append( e)
                self.errcnt+=1

            if self.stats():
                print('ERR=%s' % self.errcnt,'RX=',SI(self.srx),'TX=',SI(self.stx),self.log)

    def process(self,*argv):
        self.switch()
        print("<Thread Listening>")
        while self.serving:
            if self.Wake:
                self.step()
                while len(self.q):
                    seq,rpc = self.q.pop(0)
                    self.TX( json.dumps( [seq,rpc] ) )
            gc.collect()
            Time.sleep(.002)
        print("</Thread Listening>")











