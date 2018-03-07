#
if echo ${DESTINY}|grep ZADIG
then
    #start /drivers/zadig-2.3.exe &
    echo run > /zadig
    exit 0
fi

fel=./fel-bin/sunxi-fel.${FEL_fel}
echo "======================================================================"

#KMD5="525f4aa08778edb5569fe622f8b29524"
if echo ${FEL_DTB} |grep 'dtb' >/dev/null
then
    cmd="${fel} -p -v uboot ${FEL_SPL} \
 write 0x42000000 ml/mainline-4.12.0-rc5 \
 write 0x43000000 ${DTB} \
 write 0x43100000 ml/bootscr.${FEL_SCRMODE} \
 write 0x43300000 ${FEL_rd}
"
else
    cmd="${fel} -p -v uboot ${FEL_SPL} \
 write 0x41000000 boot/${FEL_KMD5}/*mlinuz-* \
 write 0x43000000 /tmp/fex.bin \
 write 0x43100000 /tmp/script.bin \
 write 0x50000000 ${FEL_rd}
"
fi



#0x43200000

export ADB="./adb-bin/adb.${FEL_fel} -d"


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
      ,oOKOdd0XXXXXXXXXXXXXXXXXXN0;    ${FEL_SCRMODE} + $ADB
        .,coxO0KXNXXXXXXXNXXXNXKk;    Fex = legacy/${FEL_FEX}
             .,:lxk0K000O0K0Oxo;.   U-Boot = ${FEL_SPL}

"

echo "________________________________________________________________"
#python3 uImage.py -c -A arm -C none -T script -d ${FEL_scr} ub/boot.bin
WD="`pwd`"
echo WD=${WD}

python3 -u -B ./legacy/patchfex.py patch "legacy/${FEL_FEX}" ${FEL_PATCH} > /tmp/script.fex

echo "Source boot script : ${FEL_scr}"
cp -vf "fel-bin/mkimage.${FEL_fel}" "fel-bin/sunxi-fexc.${FEL_fel}" /tmp/
cd /tmp

./mkimage.${FEL_fel} -C none -A arm -T script -d boot.scr script.bin
echo "Written boot script : /tmp/script.bin "

./sunxi-fexc.${FEL_fel} -I fex -O bin script.fex fex.bin
echo "Written fex bin : /tmp/fex.bin "


echo -n "Returning to source directory : "
cd "${WD}"
pwd

echo $cmd

if echo ${FEL_SCRMODE}|grep DBG >/dev/null
then

    echo "________________________________________________________________"
    echo "ADB=$ADB"
    env |grep H3I_|sort| tee /tmp/board.last
    env |grep FEL_|sort| tee -a /tmp/board.last
    env |grep ADB |sort| tee -a /tmp/board.last
    echo ==============================================================
else
    echo "________________________________________________________________"
fi

$cmd

if echo ${FEL_SCRMODE} | grep AOS >/dev/null
then
    exit 0
fi

echo "Board booting from RAM ..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12
do
    sleep 1
    echo -n .
done

echo
echo "Waiting Android Debug Bridge ..."

$ADB wait-for-device

$ADB forward --remove-all
$ADB reverse --remove-all
$ADB devices -l
$ADB forward tcp:2222 tcp:22
$ADB forward tcp:8266 tcp:8266
$ADB reverse tcp:9000 tcp:9000
$ADB reverse tcp:8080 tcp:8080

if [ -f "/tmp/h3droid_key" ]
then
    echo using previous ssh keypair
else
    ssh-keygen -b 1024 -t rsa -f /tmp/h3droid_key -q -N ""
fi

if echo ${FEL_SCRMODE} | grep AOE >/dev/null
then
    echo Waiting AOE ...
    sudo modprobe aoe aoe_iflist=usb0

    for i in 1 2 3 4 5 6 7 8 9 10
    do
        sleep 1
        echo > /dev/etherd/discover
    done
    exit 0
fi

echo "
Will use H3I_IMG=$H3I_IMG as installer source
"

if echo  ${FEL_SCRMODE}|grep DBG >/dev/null
then
    for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
    do
        sleep 1
        echo -n .
    done
fi

echo "Extracting MBR and PBR from SD image"
dd if=${H3I_IMG} of=/tmp/mbr_pbr bs=4194304 count=1


echo "Sending MBR and PBR to the board ramdisk"
$ADB push /tmp/mbr_pbr //tmp//mbr_pbr


if python3.4 -V
then
    export PY3="python3.4"
else
    if python3.5 -V
    then
        export PY3="python3.5"
    else
        export PY3="python3"
    fi
fi
echo "Using $PY3 as python3"
$PY3 -u -B fileserve.py 2>> /tmp/fileserve.log && stty sane || stty sane













#
