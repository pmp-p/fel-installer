#!python3 -u -B
# -*- coding: utf-8 -*-
from __future__ import with_statement
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sys

from mpycompat import *
import nanotui as nanotui
import nanotui.events as events

import glob

SOC="Hx"

RAMS = {
        'kernel_addr_r' : '0x41000000',
        'fel_scriptaddr': '0x43000000',
        'scriptaddr'    : '0x43100000',
        'ramdisk_addr_r': '0x50000000',
    }


FEL_SD = 'uboots/tools/fel-sdboot.sunxi'

SOCS = {

    'Orange PI Zero+2 H3 (Xunlong)' : {
            'SPL'       : 'ub/h3/sun8i-h2-plus-orangepi-zero',
            'H3I_UBOOT' : 'uboots/u-boot-sunxi-with-spl.bin-orangepi_zero',
            'H3I_FEX'   : 'H3/orangepizeroplus2-h3.bin',
        },

    'Orange PI Zero H2+ (Xunlong)' : {
            'SPL'       : 'ub/h3/sun8i-h2-plus-orangepi-zero',
            'H3I_UBOOT' : 'uboots/u-boot-sunxi-with-spl.bin-orangepi_zero',
            'H3I_FEX'   : 'H3/orangepizero.bin',
        },

    'Orange PI Lite (Xunlong)' : {
            'SPL'       : 'ub/h3/sun8i-h3-orangepi-lite',
            'H3I_UBOOT' : 'uboots/u-boot-sunxi-with-spl.bin-orangepilite',
            'H3I_FEX'   : 'H3/orangepilite.bin',
        },

    'Orange PI PC+ (Xunlong)' : {
            'SPL'       : 'ub/h3/sun8i-h3-orangepi-pc-plus',
            'H3I_UBOOT' : 'uboots/u-boot-sunxi-with-spl.bin-orangepi_pc_plus',
            'H3I_FEX'   : 'H3/orangepipcplus.bin',
        },

    'Orange PI + (Xunlong)' : {
            'SPL'       : 'ub/h3/sun8i-h3-orangepi-plus',
            'H3I_UBOOT' : 'uboots/u-boot-sunxi-with-spl.bin-orangepi_plus',
            'H3I_FEX'   : 'H3/orangepiplus.bin',
        },

    'Orange PI PC (Xunlong)': {
            'SPL'       : 'ub/h3/sun8i-h3-orangepi-pc',
            'H3I_UBOOT' : 'uboots/u-boot-sunxi-with-spl.bin-orangepi_pc',
            'H3I_FEX'   : 'H3/orangepipc.bin',
        },

    'Orange PI +2e (Xunlong)': {
            'SPL'       : 'ub/h3/sun8i-h3-orangepi-plus2e',
            'H3I_UBOOT' : 'u-boot-sunxi-with-spl.bin-orangepi_plus2e',
            'H3I_FEX'   : 'H3/orangepiplus2e.bin',
        },

}


DEV = os.path.exists('/c/tmp/DEV')

if 'aoe' in sys.argv:
    FEL_SCRMODE = 'AOE'
    tag= '[VBLADE]'
elif 'alpha' in sys.argv:
    FEL_SCRMODE='FNL'
    tag= '[NETWORK]'
elif 'cmd' in sys.argv:
    FEL_SCRMODE='DBG'
    tag='[A:DEBUG]'
elif 'android' in sys.argv:
    FEL_SCRMODE='AOS'
    tag='[Android]'
else:
    FEL_SCRMODE='FEL'
    tag='installer'


if DEV:
    NBD_PATH  = '/c/tmp/'
else:
    NBD_PATH= '/tmp/'

H3II_MASK = "h3droid_installer-?.?.?.img"


os.putenv('FEL_SCRMODE',FEL_SCRMODE)

def condition1(disp):
    global SOC,FEL,CID

    if UPY:
        # mpy popen makes zombies
        try:
            with open('devtest.txt','rb') as f:
                CID = f.readline().decode().strip()
                test= f.readline().decode().strip()
        except Exception as e:
            test=repr(e)
    else:
        test=os.popen('%s -l' % FEL).readline().strip()


    if test:
        while test.count('  '):
            test = test.replace('  ',' ')

        if test.count(' H5 '):
            SOC='H5'
        elif test.count(' H3 '):
            SOC='H3'
        else:
            disp('Unsupported SOC : %s'%test)
            return False

        disp(test[18:])
        return True

    disp(" * No FEL capable device found (yet) *")
    return False


def step2():
    global d,lb,kl,li,warn0, debug_lb

    items = []
    for item in glob.glob('ub/h?/sun8i-h*'):
        for elem in SOCS:
            if item in SOCS[elem].values():
                items.append( elem )

    items.sort()

    add.crlf()

    fb = add('Frame',text="Board choice :",width=-32,height=-18).valign(warn0.i,pad=1)
    lb = add('ListBox',name='uboot',items=items) #,width=90,height=90 )
    lb.reparent_to(fb,expand=True)

    items = []
    for item in glob.glob('boot/*'):
        items.append( item.rsplit('/',1)[-1] )


    kf = add('Frame',text="Kernel choice :",width=-30,height=-8, x=-40 ).halign(fb,pad=1)
    kl = add('ListBox',name='krn', items=items) #,width=90,height=90 )
    kl.reparent_to(kf,expand=True)

    df = add('Frame',text="Debug Channel :",width=-30,height=-6, x=-40 ).valign(kf,pad=1)
    debug_lb = add('ListBox',name='debug_lb', items=['/dev/tty0 (HDMI)','/dev/ttyS0 (UART)']).reparent_to(df,expand=True)
    add.crlf()

    items = []
    for item in glob.glob( NBD_PATH + H3II_MASK ):
        items.append( item.rsplit('/',1)[-1] )

    items.sort()
    items.reverse()

    fli = add('Frame',text='Version Picker:',width=-35).halign(kf,pad=1)
    li = add('ListBox',name='li',items=items)
    li.reparent_to(fli,expand=True)



    b = add('Button',name='fel', text="Start FEL", width=8,x=22,y=22)
    b.finish_dialog = events.ACTION_OK

    b.valign(df,pad=1)

    add.by_names.get('cancel').valign(fli,pad=1)



if __name__ == "__main__":
    cnt = 0
    res = 0
    step = 1
    fel = 'bin'
    CID = 0


    if nanotui.NX:
        if sys.platform=='msys':
            FEL = './fel-bin/sunxi-fel.exe -l'
            FEL_fel = 'exe'
        else:
            FEL_fel = os.popen('arch').read().strip()#'x86_64'

            FEL = './fel-bin/sunxi-fel.%s -l 2>&1' % FEL_fel
    else:
        FEL_fel = 'exe'
        FEL='fel-bin\\sunxi-fel.exe -l'

    if UPY:
        os.system('fel=%s sh ./checkdev.sh &' % FEL_fel)


    crt = None

    def panic(error=None):
        if not UPY:
            sys.stdout = sys.__stdout__
        else:
            os.system('kill -9 $(head -n 1 devtest.txt)')


    with nanotui.VisualPage('main',"H3Droid.com FEL %s" % tag,x=[4,-4],y=[4,-4]) as add:
        try:
            step = 1
            add('Label', text="--------------------------")

            f=add('Frame',text="USB Device Status",width=-45,height=-3).halign(add.last,pad=8)
            warn(f,f.width, add.last, add.last.width)
            status=add.textfill('')

            add.crlf(3)

            warn0 = add.anchor('1 - UNLOCK SD-CARD from DEVICE SLOT, or use special FEL sdcard !        ]')

            add.crlf()

            warn1 = add.anchor('2 - Link board with micro-USB *DATA* cable        ]')

            add.crlf()

            warn2 = add.anchor('3 - Reset or Power on board, while pressing FEL button if board has one     ]')

            add.crlf()

            b=add('Button', name='cancel', text="Cancel", width=8)
            b.finish_dialog = events.ACTION_CANCEL

            #add.crlf(-35)

            condition1(status)


            def step1(*argv):
                global step
                if step<2 and condition1(status):
                    step += 1
                    warn1(' ')
                    warn2(' ')
                    warn0('Select Board, then click Start')
                    step2()
                    add.redraw()

            add.handler = step1

        except Exception as e:
            print(e)
            add.End()
            panic(error=e)

    panic(None)


    if nanotui.ec['main']==events.ACTION_OK:

        ANSI_CLS = ''.join( map(chr, [27, 99, 27, 91, 72, 27, 91, 50, 74] ) )
        print(ANSI_CLS)

        KMD5 = kl.get_text()
        os.putenv('FEL_KMD5', KMD5 )


        socname = lb.get_text()
        uboot = ''

        print("Searching SPL for [%s]" % socname)
        os.putenv('H3I_BOARD', socname )


        dtb=''
        soc = SOCS[socname]

        uboot = soc['SPL']
        os.putenv('H3I_UBOOT',soc['H3I_UBOOT'] )
        os.putenv('H3I_FEX',soc['H3I_FEX'] )
        dtb=soc.get('DTB','')
        os.putenv('FEL_DTB',dtb )

        if dtb:
            os.putenv('FEL_FEX','Mainline DTB')
        else:
            os.putenv('FEL_FEX', soc['H3I_FEX'] )


        if 'android' in sys.argv:
            BOOTCMD= 'ub/android.cmd'
            os.putenv('FEL_rd', 'rd/android') #%s' % KMD5) #,KMD5) )
        else:
            os.putenv('FEL_rd', 'rd/uInitrd-hybrid')
            BOOTCMD = 'ub/boot.cmd'

        os.putenv('FEL_scr', 'ub/boot.tmp')

        print("Starting [%s] bootstrap ..." %  uboot)
        os.putenv('FEL_SPL',uboot)

        with open(BOOTCMD,'rb') as source, open('ub/boot.tmp','wb') as destination:
            data = source.read().replace(b'd41d8cd98f00b204e9800998ecf8427e',bytes( kl.get_text() , 'utf8') )
            data = data.replace(b'%H3I_FEX%' , bytes('fex/%s' % soc['H3I_FEX'],'utf8') )
            data = data.replace(b'XYZ'      ,bytes(FEL_SCRMODE[0:3], 'utf8') )
            for k in RAMS:
                data = data.replace(bytes('%%%s%%' % k,'utf8') , bytes( RAMS[k],'utf8') )
                os.putenv( k , RAMS[k] )
            destination.write( data)

        os.putenv('FEL_fel',FEL_fel)
        os.putenv('H3I_DBG', debug_lb.get_text().split(' ')[0] )


#        ACMS=[]
#
#        if sys.platform=='msys':
#            os.putenv('FEL_fel',FEL_fel)
#            os.system('echo /dev/ttyS? > ttys')
#            for i in range(1,6):
#                acm = '/dev/ttyS%s'%i
#                if not os.path.isfile(acm):
#                    ACMS.append(acm)
#        else:
#            for i in range(0,3):
#                acm = '/dev/ttyACM%s'%i
#                if not os.path.exists(acm):
#                    ACMS.append(acm)
#
#            os.putenv('FEL_fel',FEL_fel)
#
#        os.putenv('ACMS',' '.join(ACMS) )

        os.putenv('H3I_IMG',NBD_PATH + li.get_text() )

        os.system('/bin/sh booter.sh')

    else:
        print('Aborted')
