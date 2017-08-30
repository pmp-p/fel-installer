#!python3

import sys
import os


def as_fex(fn):
    srcf = open( fn , 'rb' )
    c = srcf.readline()
    if c.count( b'')>500:
        #print('BIN2FEX %s' % fn )
        srcf.close()
        srcf = os.popen('bin2fex < %s 2>/dev/null' % fn )
    else:
        srct=[]
        for line in srcf.readlines():
            srct.append( line.decode('utf8'))
        return srct
    return srcf.readlines()

SECTIONS = {}



class FEX(dict):
    def __init__(self):
        super().__init__()
        self.LAST = ' '
        self[self.LAST]={}

    def load(self,fn):
        srcf = as_fex( fn )

        for line in srcf:
            l = line.strip()
            if l:
                if l[0]=='[':
                    l = l.replace(' ','')
                    self.setdefault(l, {} )
                    self.LAST = l
                else:
                    try:
                        k,v = l.split('=',1)
                        k = k.strip()
                        v = v.strip()
                        self[self.LAST][k] = v
                    except:
                        print(l)

    def diff(self,old):
        SK = list(self.keys())
        SK.sort()
        buf = []


        for S in SK:
            olds  = old.get(S,{})
            VK = self[S]

            for ok in olds:
                if not ok in VK:
                    VK[ok]=None

            VKS = list( VK.keys() )
            VKS.sort()
            empty_sec = True

            for vk in VKS:
                tst=olds.get(vk,None)
                if tst != VK[vk]:
                    empty_sec = False
                    if ('-v' in sys.argv) or ('-vv' in sys.argv):
                        vb=''
                        if tst is None:
                            if '-vv' in sys.argv: vb="; added"
                            buf.append( '+ %s = %s%s' % ( vk , VK[vk], vb ) )
                        elif VK[vk] is None:
                            if '-vv' in sys.argv:
                                vb='\t; removed was "%s" ' % tst
                                disp = ''
                            else:
                                disp = VK[vk]
                            buf.append( '- %s = %s%s' % ( vk , disp, vb ) )
                        else:
                            if '-vv' in sys.argv:
                                vb = '\t; was "%s"' % tst
                            buf.append( '~ %s = %s%s' % ( vk , VK[vk], vb ) )
                    else:
                        buf.append( '%s = %s' % ( vk , VK[vk]) )


            if not empty_sec:
                self.out( S )
                while buf:
                    self.out( buf.pop(0) )

                self.out("")



    def dump(self):
        SK = list(self.keys())
        SK.remove('[product]')
        SK.sort()
        SK.insert(0,'[product]')


        for S in SK:
            self.out( S )
            VK = self[S]
            VKS = list( VK.keys() )
            VKS.sort()
            for vk in VKS:
                self.out('%s = %s' % ( vk , VK[vk] ) )
            self.out("")

    def out(self,s):
        print(s)

if 'diff' in sys.argv:
    src =FEX()
    src.load(sys.argv[-2])

    dst =FEX()
    dst.load(sys.argv[-1])

    dst.diff(src)

elif 'patch':
    src =FEX()
    src.load(sys.argv[-2])

#    dst =FEX()
#    dst.load(sys.argv[-2])
    src.load(sys.argv[-1])
    src.dump()


