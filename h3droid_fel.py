#!python3 -u -B
import sys
sys.path.insert(0,'.')
import nanotui
import nanotui.events as events

import glob


SOC="Hx"

SOCS = {
    "ub/h3/orangepipc.bin": {
            'name' : 'Legacy: Orange PI PC H3 (Xunlong)',
            'H3I_UBOOT': 'uboots/u-boot-sunxi-with-spl.bin-orangepi_pc',
            'H3I_FEX'  : 'H3/orangepipc.bin',
        },
    "ub/h3-ml/sun8i-h3-orangepi-pc.bin.dtb": {
            'name' : 'Mainline: Orange PI PC H3 (Xunlong)',
            'SPL' : "ub/h3/orangepipc.bin",
            'H3I_UBOOT': 'uboots/u-boot-sunxi-with-spl.bin-orangepi_pc',
            'DTB'  : 'h3-ml/sun8i-h3-orangepi-pc.bin.dtb',
        },

    "ub/h3/orangepilite.bin": {
            'name' : 'Legacy: Orange PI Lite (Xunlong)',
            'H3I_UBOOT': 'uboots/u-boot-sunxi-with-spl.bin-orangepilite',
            'H3I_FEX'  : 'H3/orangepilite.bin',
        },

}


#DEV = os.path.exists('/DEV')
DEV = 'alpha' in sys.argv

if 'debug' in sys.argv:
    os.putenv('SCRMODE','d')
    tag='[DEBUG]'
else:
    os.putenv('SCRMODE','r')
    tag='installer'

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




def step2():
    global d,lb
    items = []
    for item in glob.glob('ub/h*/*.bin'):
        if item in SOCS or DEV :
            items.append( SOCS.get(item, {'name':item} )['name'] )
    items.sort()

    lb = add('uboot','ListBox',items=items,width=44,height=15,x=3,y=5 )

    add(None,'Frame',text="Board choice :",x=2,y=4,width=lb.width+2,height=lb.height+4)


    warn(' <- Select Board Model, then start')

    link3('')

    b = add('fel','Button',text="Start FEL", width=8,x=22,y=22)
    b.finish_dialog = events.ACTION_OK


    #b = WButton(8, "h3disp")
    #d.add(30, 22, b)

    #d.set_focus( lb )

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

            add.frame("USB Device Status                          ", dx=20,dy=-3)

            status=add.anchor('-------------------------------------------\n\n\n\n\n')

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



        socname = lb.get_text()
        uboot = ''

        #print("Searching SPL for [%s]" % socname)

        if uboot.count('-ml/'):
            #mainline
            os.putenv('H3I_FEX','')
            for uboot in SOCS:
                soc = SOCS[uboot]
                if soc['name']==socname:
                    uboot = SOC['SPL']
                    os.putenv('H3I_UBOOT',soc['H3I_UBOOT'] )
                    os.putenv('DTB',soc['DTB'] )
        else:
            os.putenv('DTB','')
            for uboot in SOCS:
                soc = SOCS[uboot]
                if soc['name']==socname:
                    os.putenv('H3I_UBOOT',soc['H3I_UBOOT'] )
                    os.putenv('H3I_FEX',soc['H3I_FEX'] )
                    break

            os.putenv('FEX', uboot.replace('ub/h3','legacy/fex') )

        print("Starting [%s] bootstrap ..." %  uboot)
        os.putenv('SPL',uboot)

        if uboot.count('h3/'):
            SOC='H3'

        os.putenv('SOC',SOC)

        ACMS=[]

        if sys.platform=='msys':
            os.putenv('fel','exe')
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

            os.putenv('fel','x86_64')
        os.putenv('ACMS',' '.join(ACMS) )
        os.system('/bin/sh booter.sh')

    else:
        print('Aborted')
