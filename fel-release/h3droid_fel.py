#!python3 -u -B
# -*- coding: utf-8 -*-
from __future__ import with_statement
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division


import sys
sys.path.insert(0,'.')
import nanotui
import nanotui.events as events

import glob


SOC="Hx"

SOCS = {
    'Orange PI Lite (Xunlong)' : {
            'SPL' : "ub/h3/sun8i-h3-orangepi-lite",
            'H3I_UBOOT': 'uboots/u-boot-sunxi-with-spl.bin-orangepilite',
            'H3I_FEX'  : 'H3/orangepilite.bin',
        },

    'Orange PI PC H3 (Xunlong)': {
            'SPL' : "ub/h3/sun8i-h3-orangepi-pc",
            'H3I_UBOOT': 'uboots/u-boot-sunxi-with-spl.bin-orangepi_pc',
            'H3I_FEX'  : 'H3/orangepipc.bin',
        },

    "Orange PI +2e H3 (Xunlong)": {
            'SPL' : "ub/h3/sun8i-h3-orangepi-plus2e",
            'H3I_UBOOT': 'u-boot-sunxi-with-spl.bin-orangepi_plus2e',
            'H3I_FEX'  : 'H3/orangepiplus2e.bin',
        },

}


#DEV = os.path.exists('/DEV')
DEV = False

if 'debug' in sys.argv:
    FEL_SCRMODE='DBG'
    tag='[DEBUG]'
else:
    if 'alpha' in sys.argv:
        FEL_SCRMODE='FNL'
        tag= '[NETWORK]'
    else:
        FEL_SCRMODE='FEL'
        tag='installer'


os.putenv('FEL_SCRMODE',FEL_SCRMODE)

def condition1(disp):
    global SOC,FEL,CID

    if nanotui.UPY:
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



# mem=335M"
def step2():
    global d,lb,kl

    items = []
    for item in glob.glob('ub/h?/sun8i-h*'):
        for elem in SOCS:
            if item in SOCS[elem].values():
                items.append( elem )

    items.sort()

    lb = add('uboot','ListBox',items=items,width=30,height=15,x=3,y=5 )

    add(None,'Frame',text="Board choice :",x=2,y=4,width=lb.width+2,height=lb.height+4)


    warn(' <- Select Board Model, then start')

    link3('')


    z=2
    items = []
    for item in glob.glob('boot/*'):
        items.append( item.rsplit('/',1)[-1] )
    last =kl = add('krn','ListBox',items=items,width =35,height = lb.height-z+1,y=lb.y+z,x=40)

    add(None,'Frame',text="Kernel choice :",x=last.x-2,y=last.y-2,width=last.width+2,height=last.height)

    b = add('fel','Button',text="Start FEL", width=8,x=22,y=22)
    b.finish_dialog = events.ACTION_OK




if __name__ == "__main__":
    cnt = 0
    res = 0
    step = 1
    fel = 'bin'
    CID = 0


    if nanotui.NX:
        if sys.platform=='msys':
            FEL = './fel-bin/sunxi-fel.exe -l'
            fel = 'exe'
        else:
            fel = 'x86_64'
            FEL = './fel-bin/sunxi-fel.%s -l 2>&1' % fel
    else:
        fel = 'exe'
        FEL='fel-bin\\sunxi-fel.exe -l'

    if nanotui.UPY:
        os.system('fel=%s sh ./checkdev.sh &' % fel)


    crt = None

    def panic(error=None):
        if not nanotui.UPY:
            sys.stdout = sys.__stdout__
        else:
            os.system('kill -9 $(head -n 1 devtest.txt)')


    with nanotui.VisualPage('main',"H3Droid.com FEL %s" % tag,80, 25) as add:
        try:
            step = 1
            add(None,'Label', text="-------------------------")

            add.frame("USB Device Status                          ", dx=8,dy=-3)

            status=add.anchor('-------------------------------------------\n\n\n')

            warn = add.anchor(' 1 - UNLOCK SD-CARD from DEVICE SLOT !\n\n')

            condition1(status)


            def step1(*argv):
                global step
                if step<2 and condition1(status):
                    step += 1
                    warn(' ')
                    link(' ')
                    step2()
                    add.redraw()
                Time.sleep(.3)

            add.handler = step1


            link = add.anchor('\n\n')
            link(text='2 - Link board with micro-USB *DATA* cable')

            link3 = add.anchor('\n\n')
            link3(text='3 - Reset or Power on board')



            b=add('cancel','Button', text="Cancel", width=8,x=70,y=22)
            b.finish_dialog = events.ACTION_CANCEL

        except Exception as e:
            add.End()
            panic(error=e)

    panic(None)


    if nanotui.ec['main']==events.ACTION_OK:

        ANSI_CLS = ''.join( map(chr, [27, 99, 27, 91, 72, 27, 91, 50, 74] ) )
        print(ANSI_CLS)

        os.putenv('FEL_KMD5', kl.get_text() )

        socname = lb.get_text()
        uboot = ''

        print("Searching SPL for [%s]" % socname)
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



        print("Starting [%s] bootstrap ..." %  uboot)
        os.putenv('FEL_SPL',uboot)

        if uboot.count('h3/'):
            SOC='H3'

        os.putenv('FEL_SOC',SOC)

        ENV=b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        #env = 'mem=1G'
        env = ''
        env = '%s%s' % ( env, ' '*( len(ENV) - len(env) ) )
        with open('legacy/boot.cmd','rb') as source, open('legacy/boot.tmp','wb') as destination:
            data = source.read().replace(b'd41d8cd98f00b204e9800998ecf8427e',bytes( kl.get_text() , 'utf8') )
            data = data.replace(ENV,bytes(env,'utf8') )
            data = data.replace(b'XYZ',bytes(FEL_SCRMODE[0:3],'utf8') )
            destination.write( data)

        ACMS=[]

        if sys.platform=='msys':
            os.putenv('FEL_fel','exe')
            os.system('echo /dev/ttyS? > ttys')
            for i in range(1,6):
                acm = '/dev/ttyS%s'%i
                if not os.path.isfile(acm):
                    ACMS.append(acm)
        else:
            for i in range(0,3):
                acm = '/dev/ttyACM%s'%i
                if not os.path.exists(acm):
                    ACMS.append(acm)

            os.putenv('FEL_fel','x86_64')

        os.putenv('ACMS',' '.join(ACMS) )
        os.system('/bin/sh booter.sh')

    else:
        print('Aborted')
