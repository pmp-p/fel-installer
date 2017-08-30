try:
    UPY
except:
    print('loading compat layer')
    import sys
    sys.path.insert(0,'.')
    from mpycompat import *

port = 8266

SLEEP = .008

# MTU = 512000 #167K 1ms

#MTU = 96000     #   380(adb) 420(ip) 1ms
MTU=32000         # 480(adb)
MTU=4096          # 230(abd)
MTU=16384         # 420(adb)
MTU=57600         # 465
MTU=32500   #448
MTU=32000   #461

MTU = 65000         # 450(abd)      (423)(ip) 1ms

FMTU =  int( float(MTU)/3)*2


ticks = Lapse(1)

keep_alive_ping = Lapse(5)

if UPY:
    import os
    import uhashlib as hashlib
    import ubinascii as binascii
    from phy import ws as phy_net
    import xrpc.ureply as xreply


    phy_net.SLEEP= SLEEP

    test_critical = Lapse(4)

    reset = False


    class XIO:
        FD = {}

        @classmethod
        def select(cls,fd):
            return cls.FD[int(fd)]

        def __init__(self,fhandle,mode):
            self.fd = fhandle
            self.hasher =  hashlib.sha1()
            self.bread = 0
            self.bwrite = 0
            self.fileno = self.fd.fileno()
            self.__class__.FD[self.fileno] = self


        def write(self,payload):
            if not isinstance(payload,bytes):
                payload = payload.encode('UTF-8')
            payload = binascii.a2b_base64( payload )
            self.hasher.update( payload )
            self.fd.write(payload)
            self.bwrite += len(payload)
            return self.bwrite

        def read(self,cnt=0):
            payload = self.fd.read(cnt)
            self.hasher.update( payload )
            self.bread += len(payload)
            return binascii.b2a_base64( payload )

        def hexdigest(self):
            return binascii.hexlify( self.hasher.digest() ).lower()

        def close(self):
            hxd= self.__class__.FD.pop( self.fileno ).hexdigest()
            self.hasher = None
            try:
                self.fd.close()
            finally:
                self.fd = None
                warn('70: closed',self,hxd)
                return hxd

    def Popen(cmd,*argv):
        import usubprocess
        sp = usubprocess.spopen(cmd,*argv)
        fno = sp.fileno()
        XIO.FD[fno]=sp
        return fno

    def fopen(fn,mode='rb'):
        return XIO(  open(fn,mode) , mode ).fileno

    def fwrite(fd,payload):
        global FD
        return XIO.select(fd).write(payload)

    def fread(fd,cnt=1):
        return XIO.select(fd).read(cnt)

    def fclose(fd):
        return XIO.select(fd).close()

    def ping(*argv):
        return 'pong'

    def pipe(cmd):
        return os.popen(cmd).readlines()

    def exists(fname):
        return os.path.exists(fname)

    def do_reset(*argv):
        global reset
        reset = True


    print('\t(WS)(RPC)server')
    self=phy_net.PHY_Network_WS(port,mtu=MTU)
    while self.serving:
        reset = False
        nego, mtu = self.start()
        self.switch(nego, mtu )

        print("<Thread Listening>")
        critical = False
        while not reset:
            if keep_alive_ping:
                print('.',end='')

            if self.Wake:
                self.step()
                while len(self.q):
                    critical = False
                    rpc = self.q.pop(0)
                    seq = rpc.pop('s',-1)

                    mak = rpc.pop('m').split('.') , rpc.pop('a',()), rpc.pop('k',{}), True

                    if len(mak[0]):
                        smak = str(mak[0][0])

                    if smak[0]=="+":
                        mak[0][0]==mak[0][0][1:]
                        mak[3] = False

                    resp = xreply.do_raw(*mak)

                    if not mak[3]:
                        print('RET(%s):' % smak,repr(resp))

                    self.TX( json.dumps( [seq, resp ] ) )
                if test_critical:
                    if critical:
                        print('ATM over WS: cell timeout, restarting websocket')
                        reset = True
                    critical = True
            if UPY:gc.collect()
            Time.sleep(0.002)

        print("</Thread Listening>")

else:
    #cpython3


    import json


    class BaseRPC(bluelet.ASync):

        def write(self,method,*argv,**kw):
            global MTU
            data = json.dumps( { 's':self.mark, 'm':method , 'a':argv, 'k':kw } )
            self.phy.send( pad(data,MTU) )

        def read(self,mark):
            data = self.recv()
            while data:
                self.fifo.append( data.strip( '#' ) )
                data = ''.join(self.fifo)
                self.fifo = data.split( chr(0),1 )
                # [msga,''] or [msga,msgb]
                if len(self.fifo)>1:
                    data=self.fifo.pop(0)
                    break
                    data = ws.recv()
            if data:
                key,data = json.loads( data )
                #key,data = json.loads( self.ws.recv()[1:-1].strip() )
                self.__class__.Q[ key ] = data
                if mark in self.__class__.Q:
                    return True

    if not 'ws' in sys.argv:
        import socket

        class RPC(BaseRPC):

            def recv(self):
                global MTU
                data=self.phy.recv(125)
                if data:
                    #print("recv",len(data),data)
                    return data.decode('utf8')
                return ''

        def pad(data,sz):
            if not isinstance(data,bytes):
                data = bytes(data,'UTF-8')
            return b''.join( (b'#', data , b' '*( (sz-2) - len(data))  , b'\x00', ) )


        def client(ip,port):
            global SEQ, rpc
            sock = socket.socket()

            for ip in (ip, '127.0.0.1'):
                addr_info = socket.getaddrinfo(ip , port )
                addr = addr_info[0][-1]
                try:
                    sock.connect(addr)
                    warn('** RPC CONNNECTED TO %s:%s via %s **' % (addr,port,ip) )
                    break
                except:
                    continue

            sock.send( bytes( '%-16s' % ('MTU=%s' % str(MTU)), 'utf8' )  )
            SEQ=0
            rpc= RPC(phy=sock)
            return rpc

    else:

        import websocket
        import binascii


        def pad(data,sz):
            return ''.join( ('#', data , ' '*( (sz-2) - len(data))  , chr(0), ) )

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



        class RPC(BaseRPC):
            def recv(self):
                return self.phy.recv()


        def client(ip,port):
            global SEQ, rpc
            try:
                ws = websocket.create_connection("ws://%s:%s/" % (ip, port) )
            except Exception as e:
                print("75: falling back to localhost:%s"%port,e)
                ws = websocket.create_connection("ws://127.0.0.1:%s/" % port )

            SEQ=0
            rpc= RPC(phy=ws)
            return rpc

#==================================================================================

if __name__ == '__main__':
    asks = Lapse(4)
    port = 8266
    addr = "127.0.0.1"


    def mainloop(self):
        global rpc
        global asks
        while bluelet.threads:
            if asks:
                res = yield rpc('pipe','fdisk -l 2>&1|grep ^Disk|grep bytes|grep -v boot')
                print( res )

            else:
                Time.sleep(0.001)
                yield bluelet.null()

    def step(self):
        global ticks,PN

        while bluelet.threads:
            if ticks:
                print('.') #,end='')
                #sys.stdout.flush()
            yield bluelet.null()



    rpc = client(addr, port)
    RunTime.CoRoutines.append( mainloop )
    RunTime.CoRoutines.append( step )

    bluelet.prepare( bluelet.launcher() )

    while bluelet.threads:
        bluelet.step()

    print('bye')
