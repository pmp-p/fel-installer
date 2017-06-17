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

if false
then
    echo "Waiting for OTG UART-gadget ${ACMS} to come up ..."

    ACM='None'
    while true
    do
        if echo $ACM|grep None>/dev/null
        then
            #not bullet proof, need to build a blacklist of existing devices and checks for new only
            for acm in $ACMS
            do
                echo -n " Testing $acm "
                #if  [ -c $acm ]
                if ls /dev/tty* |grep $acm >/dev/null
                then
                    export ACM=$acm
                    break
                else
                    sleep 2
                fi
            done
            echo
        else
            break
        fi
    done
    sleep 1
    echo Sending signal on $ACM
    stty -F $ACM -opost -isig -icanon -echo raw
    sleep 1
    echo PING PING PING PING > $ACM
    echo
    clear
    echo Please Wait ...
    sleep 5
    python3 -u -B droidterm.py $ACM 115200 && stty sane || stty sane
fi

