#!python3 -u -B
try:
    UPY
except:
    import sys
    from mpycompat import *


    import time
    import os

# /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq  ?

if not './py3' in sys.path:
    sys.path.insert(0,'./py3')

stage = 1
term = None

ichoose = '/dev/null'
Tick = 0

ticks = Lapse(1)

asks = Lapse(4)

import bluelet
import websocket
import json
import ws_atm_rpc

#rpc = ws_atm_rpc.client('192.168.123.45',8266)
rpc = ws_atm_rpc.client('127.0.0.1',8266)
#rpc = ws_atm_rpc.client('192.168.0.222',8266)

import nanotui
import nanotui.events as events

lastmode = '?'

import binascii

noflicker = Lapse(2)

termfresh = Lapse(.25)

unitscan = Lapse(2)

units = None
okburn = None

def GET_BURN_UNIT():
    global units
    return str(units.get_text()).split(':',1)[0]


class rsh:
    getdisks = '/data/u-root/fel-initrd/getdisks.sh'
    getemmc  = '/data/u-root/fel-initrd/getemmc.sh'

fd_src = None

#fix erase all then fill
def boxfill(wdg,lines,ow=False):
    if ow:
        while len(wdg.items):wdg.items.pop()
    if len(lines):
        wdg.items.extend( lines )
        wdg.items_count = len( wdg.items)
        wdg.height =  wdg.items_count +1
        wdg.redraw()

def cook(wdg):
    global  h3i_ph3d, h3i_absz, ichoose, instmod
    H3I_UBOOT = os.getenv('H3I_UBOOT') # 'uboots/u-boot-sunxi-with-spl.bin-orangepi_lite'
    H3I_FEX = os.getenv('H3I_FEX') #'H3/orangepilite.bin'

    H3I_DBG = os.getenv('H3I_DBG')
    if not H3I_DBG:
        H3I_DBG = '/dev/tty0'

    scr= ["#"]

    scr.append( 'export H3I_DBG=%s\n' % H3I_DBG )
    scr.append( 'export H3I_CVBS=%s\n' % os.getenv('H3I_CVBS') )
    scr.append( 'export H3I_BOARD="%s"\n' % os.getenv('H3I_BOARD') )
    scr.append( 'export H3I_ARMBIAN=%s\n' % '' )
    scr.append( 'export H3I_ARMBIAN_SIZE=%s\n' % h3i_absz.get_text() )
    scr.append("#\n")
    if instmod.get_text()[0]=='U':
        scr.append( 'export H3I_UPGRADE_ONLY=1\n' )
        #scr.append( 'export UPGRADE_ONLY=1\n' )
    else:
        pass
        #scr.append( 'export H3I_UPGRADE_ONLY=\n' )
        #scr.append( 'export UPGRADE_ONLY=\n' )

    scr.append( 'export H3I_OUTDEV=/dev/%s\n' % ichoose )
    scr.append( 'export H3I_UBOOT=%s\n' % H3I_UBOOT  )
    scr.append( 'export H3I_FEX=%s\n' % H3I_FEX  )
    scr.append( 'export H3I_P2_SIZE=%s\n' % h3i_ph3d.get_text() )
    scr.append( "#\n")
    boxfill( wdg , scr, ow=True )

dd = None
instmod = None


def tenp(v,max,coeff = 10000):
    v*=coeff
    max*=coeff
    return int(  (max/100 * v) / coeff / coeff )

def percent(v,max):
    return int( 100.0 / max * v )


def onclick(e):
    global dd, stage, instmod, rexec, h3i

    lastmode = instmod.get_text()[0]
    if stage < 3:
        rexec = Terminal(None, text='Board Output', cols=window.void_width(pad=4), lines=window.void_height(trx.container) )
        rexec.frame.valign( trx.container, pad=1 )

    stage = 3

    if lastmode in 'DFU':
        warn( h3i.get_text() )
        if lastmode in 'DU':
            benv = h3i.items
            benv.append('')
            benv = ''.join(benv)
            warn("================= BENV ======================")
            warn(benv,end='')
            warn("================= /BENV =====================")
            import binascii
            benv = bytes(benv,'utf8')
            benv = binascii.b2a_base64( benv ).decode().strip() + '=='

            rexec.e('/data/u-root/fel-initrd/insert_coin.sh %s' % benv )
        elif lastmode in 'F':
            rexec.e( h3i.get_text() )
        else:
            warn('NOT IMPLEMENTED mode=%s' % lastmode[0] )
    else:
        rexec.e( h3i.get_text() )
    return


# dead code upython fails IO
#    if dd is not None:
#        return
#
#    class DD_FD:
#        name = '/c/tmp/h3droid_installer-1.3.0.img'
#        src = open(name,'rb')
#        size = os.stat(name)[6]
#        fd = rpc.sync('fopen','/dev/null','wb')
#        tell = 0
#        start = Time.time()
#
#
#    dd = DD_FD()
#
#    trx.set('size',dd.size)
#
#    RunTime.CoRoutines.append( coroute_test )

# d127e225fbdf2e011838754e3ed7f213784c2cc7


def coroute_test(*argv):
    global dd, trx
    written = 0
    while True:
        data = dd.src.read(ws_atm_rpc.FMTU)
        if not data:
            break
        dd.tell += len(data)
        written = yield rpc('fwrite',dd.fd, binascii.b2a_base64( data).strip().decode('UTF-8') )
        if noflicker:
            trx.update(dd, src="[%s]" % dd.name, dst="[/dev/%s]" % GET_BURN_UNIT(),size=SI(dd.tell),total=SI(dd.size) )

    h = yield rpc('fclose',dd.fd)
    trx.i.set_text("%s %s" %( written, h ) )


def boxrpc(wdg,shell,clear=False):
    global rpc,emmc
    lines=[]
    rpcdata = rpc.sync('pipe',shell)

    for line in rpcdata:
        if line.find(emmc)>0:
            line = line.replace(': ',': eMMC ')
        line = line.replace('/dev/','')
        lines.append( line.strip() )

    if clear:
        wdg.items=[]
        wdg.dirty=True

    boxfill(wdg,lines)
    return len(lines)


def onload(e):
    global emmc, rpc, trx, term
    try:
        emmc = rpc.sync('pipe',rsh.getemmc)[0].strip()
    except:
        emmc = 'ENODEV'

    warn("129: eMMC [%s]"%emmc)
    boxrpc( window['units'] , rsh.getdisks )


    trx = window.progress(text="Burn Progress %(src)s => %(dst)s  %(size)s / %(total)s  [ %(percent)s %% at %(speed)s ]")
    trx.valign(window['instfrm'],pad=1)
    trx.update(0,src="[%s]" % os.getenv('H3I_IMG','Unset') ,dst="[/dev/%s]" % GET_BURN_UNIT(),size=0,total='~300 MB')
    trx.idle( os.getenv('H3I_BOARD','env error') )

    term = Terminal(None, text='Board Kernel dmesg', cols=window.void_width('h3if'), lines=window['h3if'].height-2 )
    term.frame.halign( window['h3if'], pad=1 )
    term.e( '/data/u-root/bin/dt' )

    return True



class Terminal:
    def __init__(self,cmd,*argv,**kw):
        set = kw.setdefault
        set('width', -kw.pop('cols',80) -2 )
        set('height', -kw.pop('lines',25) -2)
        set('text','Terminal')
        self.spfd = None
        self.closed = False
        self.frame = window('Frame',**kw)
        self.screen =  window('Editor')
        self.screen.set_lines( [''] )
        self.vt = ['']
        if cmd:self.e(cmd,*argv)


    def e(self,cmd,*argv):
        if self.spfd:
            err('248: already running')
            return

        self.reset()
        self.spfd = rpc.sync('Popen', cmd,*argv)
        self.refresh = Lapse(1.0/5)
        RunTime.CoRoutines.append( self.interact )

    def reset(self):
        self.screen.reparent_to(self.frame)
        self.screen.height = self.frame.height -2
        self.screen.width = self.frame.width -2

    def interact(self,*argv):
        while not self.closed :
            if self.refresh:
                try:
                    data = rpc.sync('fread',self.spfd,64)
                    self.closed = data is None
                except Exception as e:
                    data ="IO ERROR 267: %s" % e
                    self.closed = True

                try:
                    if len(data):
                        eol = data.endswith('\n')
                        tmp = data.split('\n')
                        if len(self.vt):
                            data = [ self.vt.pop() + tmp.pop(0) ]
                            data.extend(tmp)

                            for tmp in data:
                                if tmp :
                                    self.vt.append( tmp )
                            if eol:
                                self.vt.append('')
                            while len(self.vt)> self.screen.height:
                                self.vt.pop(0)

                            self.screen.set_lines( self.vt )
                            #self.screen.dirty = True

                except Exception as e:
                    warn('200:',e)
                    self.closed = True
            yield bluelet.null()
        warn('294: closed',self)


def ui(self=None):
    global rsh, lastmode, h3i_ph3d, h3i_absz, lastb, units, h3i, instmod

    print('<app>',file=sys.stderr)
    with  nanotui.VisualPage( 'burner' ,"H3Droid.com Burner",x=[5,-5],y=[5,-5]) as add:
        try:
            add('Label', text="-------------------")

            add('Frame',text="Status", width=-65,height=-3)
            status=add.textfill('    * getting board mass storage info *')


            add.crlf(2)


            last=add('Label',text='H3Droid Size:',x=4)
            h3i_ph3d = add('InputField',name='h3i_ph3d',text='2900').halign(pad=1)
            #add.crlf()

            last=add('Label',text='Armbian Size:',x=4,y= h3i_ph3d.y)
            h3i_absz = add('InputField',name='h3i_absz',text='4096').halign() # .valign(h3i_ph3d)

            add.crlf()

            def which():
                global ichoose, lastmode
                try:
                    ichoose = GET_BURN_UNIT()
                    if okburn and okburn.set_text("Burn %s" % ichoose):
                        lastmode = '?'
                except Exception as e:
                    ichoose = 'ENODEV'
                    if okburn : okburn.set_text("Error:%s"%ichoose)

                if lastmode != instmod.get_text()[0]:
                    lastmode = instmod.get_text()[0]
                    if lastmode == 'H':
                        #boxfill( h3i , [ 'dd if=/dev/nbd0 of=/dev/%s bs=32M conv=sync' % ichoose ] + [" "*h3i.width]*10, ow=True )
                        boxfill( h3i , [ '/rd/h3iiburn.sh /dev/%s' % ichoose ] + [" "*h3i.width]*10, ow=True )
                    elif lastmode == 'F':
                        boxfill( h3i , [  '/rd/felburn.sh /dev/%s' % ichoose ] + [" "*h3i.width]*10, ow=True )
                    else:
                        cook(h3i)

            def stage2(add):
                global stage,okburn, lastb
                if stage<2:
                    okburn  = add('Button',name='okburn',text="Burn", width=8,x=10,y=22).halign(lastb, pad=2)
                    #okburn.finish_dialog = events.ACTION_OK
                    which()
                    add.set_focus(okburn)
                    stage=2


            def stepper(Pass,**kw):
                global stage, unitscan
                if stage>2:
                    return

                if unitscan:
                    res = rpc.sync('exists','/dev/mmcblk0')
                    if res:
                        u = boxrpc(units,rsh.getdisks,clear=1)
                    else:
                        if stage>1:
                            u = boxrpc(units,rsh.getdisks,clear=1)
                        stage=1
                        u = 1

                    if u>1:
                        status('%s found at least 1 unit, insert more or continue       .' % nanotui.clock() )
                    else:
                        status('%s INSERT SD-CARD\n\n'% nanotui.clock() )

                    if stage==1:
                        #FIXME: insert more

                        stage2(add)
                    elif stage==2:
                        which()
                    else:
                        #burnin
                        pass


            f_units = add('Frame',text="Target Choice :",width=20,height=-8,x=3,y=last.y+last.height+1 )
            units = add('ListBox',name='units',items=[]).reparent_to(add.last, expand=True)

            add.crlf()

            instfrm = add('Frame',name='instfrm',text="Install Mode",width=20,height=-8,x=3,y=last.y+last.height+1 )
            instfrm.valign(f_units,pad=1)

            instmod = add('ListBox',name='instmod',items=['Direct Install','Upgrade','H3ii Burn','FEL SD']).reparent_to(add.last, expand=True)

            h3if = add('Frame',name='h3if',text="Recipe",width=30,height=-14).halign(f_units,pad=1)
            h3i = add('ListBox',name='h3i',items=['#']).reparent_to(add.last, expand=True)


            add.crlf()

            c=add('Button', name='cancel', text="Abort").valign( add['h3if'], pad=1)
            c.finish_dialog = events.ACTION_CANCEL

            lastb = c = add('Button', name='rescan', text="Scan Units").halign(pad=2)
            c.finish_dialog = events.ACTION_CANCEL

            add.handler = stepper
            add.bluelet = bluelet

            res = yield add.blueloop(0.04)

        except Exception as e:
            add.End(error=e)
            raise e
        RunTime.wantQuit = True


    print('</app>',file=sys.stderr)
    if nanotui.ec.get('burner') != events.ACTION_OK:
        #tstat = add.frame("Transfer Progress of %s MB to %s       " % (str(bm),MSGP) ,x=2,dy=2)
        print('exit code:',nanotui.ec.get('burner'))
    rpc.write('do_reset')

def step(self):
    global ticks,PN

    while bluelet.threads:
        if ticks:
            print('.',file=sys.stderr,end='')
            sys.stderr.flush()
            pong = yield rpc('ping')
            assert pong=='pong'
        else:
            yield bluelet.null()



RunTime.CoRoutines.append( step )
RunTime.CoRoutines.append( ui )

bluelet.prepare( bluelet.launcher() )

while not RunTime.wantQuit and bluelet.threads:
    bluelet.step()
