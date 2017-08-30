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

class spopen:
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
        if UPY:
            self.stdin, self.__stdout, self.__stderr, self.pid = popen3(self.cmd, stdin = self.running )
            self.stdout = fkio(self.__stdout)
        else:
            err('103: FIXME: plz use standard python3 subprocess lib')
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
                    self.terminate(reason='no more data')
                    break
                if self.running:
                    with self.stdout.lock:
                        self.stdout.pipe(data)
                Time.sleep(.001)
            except Exception as e:
                if self.running:err("TRAP:",e)
                #data = '_'

    def pipe(self,data):
        if not isinstance(data,bytes):
            data = bytes( data , 'utf8')
        try:
            return self.stdin.write(data)
        except:
            err('99: broken pipe')
            self.terminate(reason="broken pipe")

    write = pipe

    def communicate(self,input=None,timeout=None):
        if input:
            self.pipe(input)
        return self.stdout.read().decode(), ''



    def read(self,n=0):
        #FIXME: buffering
        if self.running:
            return self.stdout.read()
        return ''


    def terminate(self,reason='?'):
        try:
            self.stdin.close()
        except:
            pass
        finally:
            warn('151: [%s] termination "%s"' % (self.cmd, reason))
            if self.running:
                io = self.running
                self.cmd = self.running = self.stdin = self.stdout = None
                self.__stdout.close()
                os.unlink( io )
        #SIGTERM
        #FIXME: os.kill(self.pid,9)

        gc.collect()

    kill = terminate

    def poll(self):
        if self.running is None:
            # returncode ?
            return True
        return None


if __name__ == '__main__':
    import sys
    sys.path.append('.')
    from mpycompat import *


    ticks = Lapse(1)

    go = Lapse(2)

    sp = spopen('./test_subpro.sh',bufsize=0)
    p = 0
    print("================")
    while sp.poll() is None:
        #print(sp)
        if ticks:
            p+=1
            print('.',end='')
            if p>10:
                sp.terminate(reason="killed")
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
