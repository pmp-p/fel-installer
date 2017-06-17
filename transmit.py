import sys
import nanotui
import nanotui.events as events

nanotui.W32 = sys.platform.startswith('msys')

#import io
#import serial

import glob
import zipfile

stage = 1

TTY= '/dev/null'

def get_bundlet(fname):
    import tarfile
    bundle = tarfile.open(fname,'r')
    btotal = 0
    bfiles = []
    for m in bundle.getmembers():
        #print(m.name,m.size)
        btotal += m.size
        bfiles.append( m.name )
    return bfiles,btotal

def get_bundlez(fname):
    import zipfile
    btotal = 0
    bfiles = []

    with zipfile.ZipFile(fname) as zip:
        for zil in zip.infolist():
            if not zil.filename.endswith('/'): #zil.is_dir() > 3.6
                btotal += zil.file_size
                bfiles.append( zil.filename )
    return bfiles,btotal




with nanotui.VisualPage('installer',"H3Droid.com Board OTG installer File Transfer",80, 25) as add:
    try:
        def stage1(clk):
            global MSGD,MSGP
            drives = []

            #msys
            if nanotui.W32:
                for drive in range(2,26):
                    drive = chr( ord('a')+drive)
                    if os.path.isdir('/%c' % drive ):
                        drives.append( drive )

                for drive in drives:
                    if os.path.isfile('/%c/H3Droid.com' % drive ):
                        return stage2_pre(clk,drive)

                drives= ','.join( drives )
                status('%s waiting for boot complete, %s' % ( clk, drives ) )
                return

            #ubuntu/mint /media/*/H3DROID/
            for wildpath in '/media/*/H?DROID/H?Droid.com /mnt/*/H?Droid.com /mnt/*/H?DROID/H?Droid.com'.split(' '):
                for udrv in glob.glob(wildpath):
                    MSGP = udrv.rsplit('H3Droid.com',1)[0]
                    return stage2_pre(clk,MSGP)
            status('Waiting for /media/*/H3DROID')

        def stage2_pre(clk,drive):
            global MSGD, MSGP, stage
            MSGD=drive
            b = add('tx','Button',text="Transmit to Board", width=8,x=10,y=22)
            b.finish_dialog = events.ACTION_OK
            if not nanotui.W32:
                status('%s Ready to TX on %s' % (clk, MSGP ) )
            else:
                status('%s Ready to TX on virtual drive %c:' % (clk, MSGD.upper() ) )
            add.redraw()
            stage = 2

        def stage2():
            pass


        def update(Pass):
            global stage
            clk = nanotui.clock()

            if stage==1:
                stage1(clk)
                add.redraw()
            elif stage==2:
                stage2()
            Time.sleep(.1)



        add.handler=update

        add.frame("Board status                                               ",x=2,dy=2)
        status=add.anchor('--------------------------------------------------------')

        status('boot')


        ilist = glob.glob('/tmp/h3droid_installer-?.*.zip')

        if not nanotui.W32:
            ilist.extend( glob.glob('../h3droid-fel-w32/w32support/tmp/h3droid_installer-?.*.tar'))

        ilist.extend(glob.glob('/tmp/h3droid_installer-?.*.tar'))

        ilist.sort()
        ilist.reverse()

        ichoose = last = add('term1','ListBox',items=ilist,width=70,height=8,x=3,y=10 )
        add(None,'Frame',text="Source Choice :",x=last.x-2,y=last.y-2,width=last.width+2,height=last.height+4)


        c=add('cancel','Button', text="Abort", width=8,x=60,y=22)
        c.finish_dialog = events.ACTION_CANCEL

    except Exception as e:
        add.End(error=e)



if nanotui.ec['installer'] != events.ACTION_OK:
    raise SystemExit

ichoose = ichoose.get_text().strip()

with nanotui.VisualPage('transfer',"H3Droid.com Board OTG installer File Transfer",80, 25) as add:
    try:
        add.redraw()

        import hashlib

        if nanotui.W32:
            DEST = '/%c/i.tar' % MSGD
            SHTRIGGER = '/%c/trigger' % MSGD
            SHFINAL = '/%c/felcmd.sh' % MSGD
        else:
            DEST = '/%s/i.tar' %  MSGP
            SHTRIGGER = '/%s/trigger' %  MSGP
            SHFINAL = '/%s/felcmd.sh' % MSGP


        class HashCopier:
            def __init__(self,ifname=None ,ofname = None,ifd=None,ofd=None,chunk=65536, hasher=hashlib.md5, sync =False):
                self.chunk = chunk
                self.ifile = ifd or open(ifname,'rb')
                self.ofile = ofd or open(ofname,'wb')
                self.blocks = 0
                self.sync = sync
                if isinstance(hasher,str):
                    #import hashlib
                    hasher = getattr( hashlib , hasher.lower() )()
                if hasher is None:
                    self.hr = None
                    return
                self.hr = hasher or hasher()

            def next(self):
                data = self.ifile.read(self.chunk)
                if data:
                    if self.hr:
                        self.hr.update(data)
                    self.ofile.write(data)
                    if not self.blocks % 64:
                        if self.ofile and self.sync :
                            self.ofile.flush()
                            os.fsync(self.ofile)
                    self.blocks+=1
                    return len(data)

                if self.ofile:

                    self.ofile.flush()
                    if self.sync : os.fsync(self.ofile)
                    self.ofile.close()

                self.ifile.close()

                self.ofile = self.ifile = None

                if self.hr:
                    self.hash = self.hr.hexdigest().lower()
                return None

        copier = None


        if ichoose.endswith('zip'):
            bfiles,btotal = get_bundlez(ichoose)

            with zipfile.ZipFile( ichoose ) as zip:
                for bf in bfiles:
                    with zip.open(bf) as ifd:
                        print(bf)
                        copier = HashCopier(ifd=ifd, ofname='/%c/%s'%(MSGD, bf.rsplit('/')[-1]), hasher=None)
                        while copier.next():
                                pass

        elif ichoose.endswith('tar'):
            bfiles,btotal = get_bundlet(ichoose)
            bm= int(btotal/1024/1024)
            if not nanotui.W32:
                tstat = add.frame("Transfer Progress of %s MB to %s       " % (str(bm),MSGP) ,x=2,dy=2)
            else:
                tstat = add.frame("Transfer Progress toward %c: Size = %s MB               " % (MSGD,str(bm)) ,x=2,dy=2)
            progress=add.anchor('                                                     ')

            add.frame("MD5 Check",dx=+6,dy=-1)
            md5status= add.anchor('--------')

            c=add('cancel','Button', text="Abort", width=8,x=60,y=22)
            c.finish_dialog = events.ACTION_CANCEL

            copier = HashCopier(ifname=ichoose, ofname= DEST, hasher='md5', sync=True)
            blocks = btotal / progress.width
            while copier.next():
                add.step()
                if progress('X' * int( ( copier.blocks * copier.chunk ) / blocks ) ):
                    add.redraw()

            md5status('passed')



        with open(SHFINAL,'wb') as sh:
            y,my,d,h,m,s = Time.localtime( Time.time() )[:6]
            sh.write(b"#\n")
            sh.write( bytes('date -s "%s-%s-%s %s:%s:%s"\n' % (y,my,d,h,m,s),'utf8') )
            sh.write( bytes('export H3I_FEX=%s\n' % os.getenv('H3I_FEX'),'utf8') )
            sh.write( bytes('export H3I_UBOOT=%s\n' % os.getenv('H3I_UBOOT') ,'utf8') )
            sh.write(b"#\n")
            sh.flush()
            os.fsync(sh)



        ACMS= []


        if sys.platform=='msys':
            for i in range(1,6):
                acm = '/dev/ttyS%s'%i
                if not os.path.exists(acm):
                    ACMS.append(acm)
        else:
            for i in range(0,3):
                acm = '/dev/ttyACM%s'%i
                if not os.path.exists(acm):
                    ACMS.append(acm)

        if not nanotui.W32:
            dev = os.popen("grep '/H3DROID ' /proc/mounts |cut -f1 -d' '").read().strip()
        else:
            dev="%c:" % MSGD


        #trigger otg msg=>serial
        with open(SHTRIGGER,'wb') as sh:
            sh.write(b'done')

        #try to eject
        if nanotui.W32:
            #ask for UAC
            os.system('/nircmd elevate /freeeject.exe %c:' % MSGD )

        elif dev:
            os.system('udisks --unmount %s' % dev)
            os.system('udisks --eject %s' % dev)

        Time.sleep(2)

        tstat.set_text('Board Control channels %s' % dev)

        def stage3(add):
            global stage
            progress('Found control channel at %s' % TTY )
            b = add('fel','Button',text="Start Installer", width=8,x=10,y=22)
            b.finish_dialog = events.ACTION_OK
            stage=3


        def wait_for_serial(Pass,**kw):
            global TTY,ACMS
            if stage<3:
                progress('%s * Waiting for otg serial link to appear *' % nanotui.clock() )

                for acm in ACMS:
                    if os.path.exists(acm):
                        TTY=acm
                        return stage3(add)

        add.handler = wait_for_serial

    except Exception as e:
        add.End(error=e)

os.system('clear')

print('Please Wait on %s ...' % TTY )
for i in range(0,3):
    print('Connecting ... ')
    Time.sleep(1)
print()
if TTY=='/dev/null':
    print("""

    NOTE: if you got stuck here then you probably need to install windows driver for Linux Gadget 2.4
    with device manager.

""")
print("""
    WARNING:

        In the next 15 seconds ( or if you had time to read all that ) :
        If screen does not clear and continue to burner dialog :
        then you have hit the nasty otg bug of kernel 3.4.113.
        Only way to pass that is : power reset the board and try again.

    Please note that this bug is *totally random* and may require lot of trials
    Sorry we don't have anything better at the moment ...

""")
print()
exec( compile(open('droidterm.py').read(), 'droidterm', 'exec'), globals() ,locals() )











#
