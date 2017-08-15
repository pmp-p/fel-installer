# -*- coding: utf-8 -*-
from __future__ import with_statement
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sys
import builtins


builtins.sys = sys
builtins.builtins = builtins

impl = sys.implementation.name[:3]
if impl=='mic':
    impl='upy'
    builtins.UPY = True
else:
    builtins.UPY = False

dirname = __file__.rsplit('mpycompat',1)[0]
sys.path.insert(0,'%s/xpy' % dirname )
sys.path.insert(0,'%s/xpy/%s' % ( dirname , impl ) )
del dirname


if UPY:
    import ujson as json
    import utime as time
    def ticks_us():return time.ticks_us()
    import _thread
    import gc
    def do_gc(v=False):gc.collect()
    import ubluelet as bluelet

else:
    import json
    import time
    def ticks_us(): return int(time.time() * 1000000)
    def do_gc(v=False):pass
    import bluelet

import os
import os.path

protect = ['RunTime']

class select:
    ioq = {}
    iow = []

    @classmethod
    def select(cls,rl,wl,xl,timeout=0):
        fd=rl[0]
        fdid=id(fd)
        if not fdid in cls.ioq:
            cls.ioq[fdid]=[]
            cls.iow.append( iowait(fd, len(cls.iow)+1 ) )

        return [len( cls.ioq[fdid] )]

    @classmethod
    def readall(cls,fd):
        buf=b''
        fdid=id(fd)
        while len(select.ioq[fdid]):
            buf += select.ioq[fdid].pop(0)
        return buf

if UPY:
    builtins.select  = select


class iowait:

    select = select

    def __init__(self,fd,tid):
        self.fd = fd
        _thread.start_new_thread(self.run,[tid,0])

    def run(self,*argv):
        fdid=id(self.fd)
        while True:
            try:
                if 0:
                    self.select.ioq[fdid].append( self.fd.read(1) )
                else:
                    d=os.read(0,1)
                    if d:
                        self.select.ioq[fdid].append( d )

            except Exception as e:
                print(self.fd,e)
                return




def isDefined(varname,name=None):
    if not hasattr(__import__(name or __name__),varname):
        try:
            eval(varname)
        except NameError:
            return False
    return True

class robject(object):
    def ref(self):
        RunTime.CPR[id(self)]=self
        try:
            tips=self.to_string()
        except:
            try:
                tips= str( self )
            except:
                tips=object.__repr__(self)
        return 'µO|%s|%s' % ( id(self) , tips )

#TODO: unref

    def __repr__(self):
        if not RunTime.SerFlag:
            try:
                return self.to_string()
            except:
                return object.__repr__(self)
        return self.ref()

def noop(*argv,**kw):pass

class Debugger:

    def unhandled_coroutine(self,tb):
        if UPY:
            print("\n\033[31mCoroutine handling the faulty code has been killed",tb,file=sys.stderr)
        else:
            import traceback
            traceback.print_exc(file=sys.stderr)



class RunTime:

    SerFlag = 0
    COMRATE = 115200
    COMPORT = '/dev/ttyGS0'

    CPR = {}

    Timers = {}

    CoRoutines = []

    builtins = builtins
    IP = '0.0.0.0'

    urpc = None

    srv = 'http://192.168.1.66/mpy'

    ANSI_CLS = ''.join( map(chr, [27, 99, 27, 91, 72, 27, 91, 50, 74] ) )

    SSID = 'SSID'
    WPA = 'password'

    webrepl = None
    server_handshake = None
    server_http_handler = None

    I2C_FOLLOWER = 0x0

    MEM_init = 32678

    wantQuit = False

    @classmethod
    def add(cls,entry,value):
        global protect
        setattr(builtins,entry,value)
        if not entry in protect:
            protect.append(entry)

    @classmethod
    def to_json(cls,data):
        cls.SerFlag += 1
        try:
            return json.dumps(data)
        finally:
            cls.SerFlag -= 1

    debugger = Debugger()


    unset = object()


def logger(*argv,**kw):
    for arg in argv:
        print(arg,end=' ',file=sys.stderr)
    print('',file=sys.stderr)
    if not UPY:
        sys.stderr.flush()
    #os.fsync(sys.stderr.fileno())

def SI(dl,bw=False):
    u = 'B/s'
    dl = float(dl)
    if bw:
        for u in ['KB/s','MB/s','GB/s']:
            dl = dl/1024
            if dl<1024:
                return '%0.2f %s' % (dl,u )
        return '%s %s' %( dl,u )

    for u in ['K','M','G']:
        dl = dl/1024
        if dl<1024:
            return '%0.2f %sB' % (dl,u )
    return '%s %s' %( dl,u )

class Lapse:
    def __init__(self,intv=1.0,oneshot=None):
        self.cunit = intv
        self.intv = int( intv * 1000000 )
        self.next = self.intv
        self.last = ticks_us()
        self.count = 1.0
        if oneshot:
            self.shot = False
            return
        self.shot = None

#FIXME: pause / resume(reset)

    def __bool__(self):
        if self.shot is True:
            return False

        t = ticks_us()
        self.next -= ( t - self.last )
        self.last = t
        if self.next <= 0:
            if self.shot is False:
                self.shot = True
            self.count+= self.cunit
            self.next = self.intv
            return True

        return False

RunTime.add('SI', SI )
RunTime.add('Lapse', Lapse )


builtins.os = os
builtins.bluelet = bluelet
builtins.Time = time
builtins.sys = sys
builtins.RunTime = RunTime
builtins.use = RunTime
builtins.isDefined = isDefined
builtins.robject = robject
builtins.do_gc = do_gc


builtins.fix = logger
builtins.warn = logger
builtins.dev = logger
builtins.err = logger
builtins._info = builtins.info = logger
