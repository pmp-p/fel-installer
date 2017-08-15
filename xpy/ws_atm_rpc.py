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


go = Lapse(2)

import _thread

class fkio:
    def __init__(self,io):
        self.q = []
        self.io = io
        self.lock = _thread.allocate_lock()


    def read(self):
        with self.lock:
            try:
                return b''.join( self.q )
            finally:
                self.q=[]
        return b''


    def pipe(self,data):
        if not isinstance(data,bytes):
            data = bytes( data , 'utf8')
        self.q.append(data)



def popen3(cmd, mode="rwe", stdin = None):
    import builtins
    from os import fork,close,dup,system,_exit,pipe
    i, o = pipe()
    if mode[0] == "w":
        i, o = o, i
    pid = fork()
    if pid:
        close(o)
        po = builtins.open(i, 'rb')
        pi = builtins.open( stdin , 'wb')
        pe = None #stderr someday
        return pi, po, pe, pid

    if mode[0] == "r":
        close(1)
    else:
        close(0)
    close(i)
    dup(o)
    close(o)
    if stdin:
        s = system('<'.join( (cmd,stdin) ) )
    else:
        s = system(cmd)
    _exit(s)

class subprocess:
    fifono = 0

    def __init__(self,bin,*argv,**kw):
        self.__class__.fifono -=1
        self.running = '/tmp/upy.%s'% abs(self.__class__.fifono)

        if os.access(self.running, os.F_OK):
            os.unlink(self.running)
        os.system('mkfifo %s' % self.running)
        argv='"'.join( map(str,argv) )
        if argv:
            argv=' "%s" '%argv
        self.cmd = '%s%s' % (bin,argv)
        self.stdin, self.__stdout, self.__stderr, self.pid = popen3(self.cmd, stdin = self.running )
        self.stdout = fkio(self.__stdout)
        print( self.stdin, self.stdout )
        self.q = []
        #os.system('echo -n > %s' % self.running )
        _thread.start_new_thread( self.run , () )

    def fileno(self):
        return self.__class__.fifono

    def run(self):
        while self.running:
            try:
                data = self.__stdout.read(1)
                if not data:
                    self.terminate()
                    break

            except Exception as e:
                if self.running:err("TRAP:",e)
                data = '_'

            if self.running:
                with self.stdout.lock:
                    self.stdout.pipe(data)


    def pipe(self,data):
        if not isinstance(data,bytes):
            data = bytes( data , 'utf8')
        try:
            return self.stdin.write(data)
        except:
            self.terminate()

    write = pipe

    def communicate(self,input=None,timeout=None):
        if input:
            self.pipe(input)
        return self.stdout.read().decode(), ''



    def read(self,n=0):
        #FIXME: buffering
        return self.stdout.read()


    def terminate(self):
        try:
            self.stdin.close()
        except:
            pass
        finally:
            warn('151: [%s] termination' % self.cmd)
            if self.running:
                io = self.running
                self.cmd = self.running = self.stdin = self.stdout = None
                self.__stdout.close()
                os.unlink( io )
        gc.collect()

    kill = terminate

    def poll(self):
        if self.running is None:
            # returncode ?
            return True
        return None


if 0:
    sp = subprocess('cat',bufsize=0)
    p = 0
    print("================")
    while sp.poll() is None:
        #print(sp)
        if ticks:
            p+=1
            print('.',end='')
            if p>10:
                sp.terminate()
                break
        ro,re=sp.communicate()
        if ro:
            print(ro,end='')

        if go:
            print(p,sp.poll())
            sp.pipe(b'TEST'*20+b'\n')

        Time.sleep(.01)
    print("================")

    Time.sleep(2)
    raise SystemExit


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
        return XIO( subprocess(cmd,*argv) ).fileno

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
            if self.Wake:
                self.step()
                while len(self.q):
                    critical = False
                    rpc = self.q.pop(0)
                    seq = rpc.pop('s',-1)
                    mak = rpc.pop('m').split('.') , rpc.pop('a',()), rpc.pop('k',{})
                    if len(mak[0]):
                        smak = str(mak[0][0])
                    resp = xreply.do_raw(*mak)
                    if smak not in ['ping','fwrite']:
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
