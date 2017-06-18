#

fel=./fel-bin/sunxi-fel.${fel}
echo "======================================================================"

if echo ${DTB} |grep '\-ml' >/dev/null
then
    cmd="${fel} -p -v uboot ${SPL} \
 write 0x42000000 ml/mainline-4.12.0-rc5 \
 write 0x43000000 ${DTB} \
 write 0x43100000 ml/bootscr.${SCRMODE} \
 write 0x43300000 rd/uInitrd-hybrid"

else
    cmd="${fel} -p -v uboot ${SPL} \
 write 0x42000000 legacy/vmlinuz-3.4.113-sun8i \
 write 0x43000000 ${FEX} \
 write 0x43100000 legacy/bootscr.${SCRMODE} \
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

$cmd


echo "======================================================================"

echo -n "Waiting for OTG MSG to come up ..."
python3 -u -B transmit.py && stty sane || stty sane
