try:
    UPY
except:
    print('loading compat layer')
    import sys
    sys.path.insert(0,'.')
    from mpycompat import *

if UPY:
    import ujson as json
    import ubinascii as binascii
    import utime as Time
    import os
    import usocket as socket

    socket_error = os.error

    def ticks_us():return Time.ticks_us()

else:
    import json
    import binascii
    import time as Time
    import socket

    socket_error = socket.error

    def ticks_us(): return int(Time.time() * 1000000)


#ATM8B=508
ATM8B=1117 # //4 + 1
#ATM8B=2044
#ATM8B=3000 #4000
#ATM8B=6000 #8000
#ATM8B=9000
#ATM8B=92 #124

lt=0
cumul=0

DBG=0


def calibrate(mtu,payload=2):
    cal = mtu // 2
    mtu = mtu - payload
    cal64 = 0
    enc = b''

    while cal64<mtu:
        cal+=1
        enc = binascii.b2a_base64( b' '*cal).strip().strip(b'=')
        cal64 = len(enc)
    return cal


calibrate(1492)

def pad(data,sz):
    return ''.join( ('#', data , ' '*( (sz-2) - len(data))  , chr(0), ) )


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]


class Lapse(Lapse):

    def bw(self,dl):
        u = 'B/s'
        dl = float(dl)
        for u in ['KB/s','MB/s','GB/s']:
            dl = dl/1024
            t = dl/self.count
            if t<1024:
                return '%0.2f %s' % (t,u )
        return '%s %s' %( int(dl/self.count),u )


class TXRX:

    def setup(self,sock,stats=False,ticks=10):
        self.sock = sock
        if stats:
            self.ticks = Lapse(ticks)
            self.stat= True
            self.srx = 0
            self.stx = 0
            return
        self.stat= False


    def RX(self):
        if not self.stat:return self.sock.recv(self.MTU)
        data= self.sock.recv(self.MTU)
        self.srx += len(data)
        return data

    def TX(self,data):
        if not self.stat:return self.sock.send(data)
        self.stx +=len(data)
        self.sock.send(data)


    def stats(self):
        if self.ticks:
            print("\n", self.ticks.bw(self.srx) , '     ', self.ticks.bw(self.stx) )
            return True




class PHY_Network(TXRX):


    def __init__(self,port,addr="0.0.0.0",mtu=1492):
        global sock
        self.port = int(port)
        self.client = None
        self.serving=True
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        ai = socket.getaddrinfo(addr, port)
        addr = ai[0][4]
        sock.bind(addr)

        sock.listen(.001)
        sock.setblocking(True)
        self.MTU = mtu

    def start(self):
        global sock
        print("<Thread Serving at", self.port,'>')
        while self.serving:
            self.client = None
            try:
                #with lock:
                self.client, self.address = sock.accept()
            except socket_error as e:
                if e.args[0]==11:
                    continue
                else:
                    print("159:",e)
            except KeyboardInterrupt:
                self.serving = False
                print("46: exit request")
                return
            print("client connected ",self.address)
            #handshake(self.client)
            break
        self.setup(self.client,True)

        print("</Thread Serving>")


    def process(self,*argv):
        if not self.serving:
            print("58: early exit")
            return
        print("<Thread Listening>")
        while self.serving:
            self.TX( self.RX() )
            self.stats()
        print("</Thread Listening>")



if __name__=='__main__':

    SLEEP = .001
    port = 8266
    addr = "127.0.0.1"

    MTU = 1492
    MTU = 65500




    print(sys.argv)
    if 'srv' in sys.argv:
        if 'ws' in sys.argv:
            print('\t(WS)SERVER')
            from phy import ws as phy_net
            phy_net.SLEEP = SLEEP
            pn=phy_net.PHY_Network_WS(port,mtu=MTU)
        else:
            print('\tSERVER')
            pn=PHY_Network(port)
        pn.start()
        pn.process()

    else:

        PAD = calibrate(MTU)

        if 'ws' in sys.argv:
            fifo = []
            print('\t(WS)CLIENT')
            url = "ws://%s:%s/"  % ( addr,port)

            if UPY:
                import uwebsockets
                ws = uwebsockets.client.connect( url )

            else:

                import websocket
                ws = websocket.create_connection(url)

            for SEQ in range(1,1000*1000):
                data = json.dumps( [SEQ,'x' * (MTU-10) ] )
                ws.send( pad(data,MTU) )
                Time.sleep(SLEEP)
                data = ws.recv()
                while data:
                    fifo.append( data.strip( '#' ) )
                    data = ''.join(fifo)
                    fifo = data.split( chr(0),1 )
                    # [msga,''] or [msga,msgb]
                    if len(fifo)>1:
                        data=fifo.pop(0)
                        #print(len(data), json.loads(data) and True )
                        #end of queue any more read would block
                        break
                    data = ws.recv()

        else:
            print('\tCLIENT')


            addr_info = socket.getaddrinfo(addr , port )
            addr = addr_info[0][-1]
            s = socket.socket()
            s.connect(addr)
            for i in range(0,1000*1000):
                s.send(b' '*PAD)
                Time.sleep(SLEEP)
                data = s.recv(MTU)

    raise SystemExit






