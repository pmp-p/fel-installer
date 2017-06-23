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
 write 0x43300000 rd/uInitrd-hybrid"

else
    cmd="${fel} -p -v uboot ${FEL_SPL} \
 write 0x42000000 boot/${FEL_KMD5}/*vmlinuz* \
 write 0x43000000 legacy/${FEL_FEX} \
 write 0x43100000 legacy/boot.bin \
 write 0x43300000 rd/uInitrd-hybrid"
fi



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
      ,oOKOdd0XXXXXXXXXXXXXXXXXXN0;    SOC = $SOC
        .,coxO0KXNXXXXXXXNXXXNXKk;    Fel = $fel
             .,:lxk0K000O0K0Oxo;.   U-Boot = $SPL

"

echo "________________________________________________________________"
#python3 uImage.py -c -A arm -C none -T script -d legacy/boot.cmd legacy/boot.bin
./fel-bin/mkimage.${FEL_fel} -C none -A arm -T script -d legacy/boot.tmp legacy/boot.bin
if echo ${FEL_SCRMODE}|grep DBG>/dev/null
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
echo -n "Waiting for OTG MSG to come up ..."
python3 -u -B transmit.py && stty sane || stty sane
