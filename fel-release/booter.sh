#

fel=./fel-bin/sunxi-fel.${FEL_fel}
echo "======================================================================"

#KMD5="525f4aa08778edb5569fe622f8b29524"
if echo ${FEL_DTB} |grep 'dtb' >/dev/null
then
    cmd="${fel} -p -v uboot ${FEL_SPL} \
 write 0x42000000 ml/mainline-4.12.0-rc5 \
 write 0x43000000 ${DTB} \
 write 0x43100000 ml/bootscr.${FEL_SCRMODE} \
 write 0x43300000 ${FEL_rd}"

else
    cmd="${fel} -p -v uboot ${FEL_SPL} \
 write 0x41000000 boot/${FEL_KMD5}/*vmlinuz* \
 write 0x43000000 legacy/${FEL_FEX} \
 write 0x43100000 ub/boot.bin \
 write 0x50000000 ${FEL_rd}"
fi



#0x43200000


echo "\
            .;.                .;,
           .dKOdc.          .;ok00:
           ,0K0KK0o:;::::::lOXK00Xx.
           :KXKKXXXXXXXXXXXXXXXKKXO.
           ,0XXK  | KXXXXXX  |  XN0,
           ,ON0  [   kXXXXf   ]  XXo.
        __-lKXK      k H 0O      XXx;-__
            OXXXNXXKOO 3 OOKXXXXXKO-__
 xd      __--',coxOOkkOOOOO0Okdl,.
dNXl             .cdddddddddo,
xNKc             ;KNXXXXXXXXXk.
xNK:            .xXXXXXXXXXXXXo.
oXK:            :KXXXXXXXXXXXX0:    ╭╮╱╭╮╭━━━╮╭━━━╮╱╱╱╱╱╱╱╱╱╱╱╭╮
:KXl           .kXXXXXXXXXXXXXXk.   ┃┃╱┃┃┃╭━╮┃╰╮╭╮┃╱╱╱╱╱╱╱╱╱╱╱┃┃
'ONk.          lKXXXXXXXXXXXXXXXo.  ┃╰━╯┃╰╯╭╯┃╱┃┃┃┃╭━╮╭━━╮╭╮╭━╯┃
 lXXl.        ,OXXXXXXXXXXXXXXXX0:  ┃╭━╮┃╭╮╰╮┃╱┃┃┃┃┃╭╯┃╭╮┃┣┫┃╭╮┃
 .oKKl.      .dXXXXXXXXXXXXXXXXXXk. ┃┃╱┃┃┃╰━╯┃╭╯╰╯┃┃┃╱┃╰╯┃┃┃┃╰╯┃
   :0Xk,     cKXXXXXXXXXXXXXXXXXXK: ╰╯╱╰╯╰━━━╯╰━━━╯╰╯╱╰━━╯╰╯╰━━╯
    'dKKd;. .kXXXXXXXXXXXXXXXXXXXXl
      ,oOKOdd0XXXXXXXXXXXXXXXXXXN0;    ${FEL_SCRMODE}
        .,coxO0KXNXXXXXXXNXXXNXKk;    Fex = legacy/${FEL_FEX}
             .,:lxk0K000O0K0Oxo;.   U-Boot = ${FEL_SPL}

"

echo "________________________________________________________________"
#python3 uImage.py -c -A arm -C none -T script -d ub/boot.cmd ub/boot.bin
./fel-bin/mkimage.${FEL_fel} -C none -A arm -T script -d ${FEL_scr} ub/boot.bin
if echo ${FEL_SCRMODE}|grep DBG >/dev/null
then
    echo $cmd
    echo ==============================================================
    env |grep H3I|sort
    env |grep FEL_|sort
    echo ==============================================================
    $cmd
    sleep 30
else
    $cmd
fi

if echo ${FEL_SCRMODE} | grep AOS >/dev/null
then
    exit 0
fi

if echo ${FEL_SCRMODE} | grep AOE >/dev/null
then
    echo Waiting board ...
    sleep 15
    sudo modprobe aoe aoe_iflist=usb0
else
    echo -n "Waiting for OTG MSG to come up ..."
    python3 -u -B transmit.py && stty sane || stty sane
fi
