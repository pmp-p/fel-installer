#!/bin/bash
for conf in configs/orangepi_*
do
    grep CONFIG_DEFAULT_DEVICE_TREE $conf > /tmp/uconf
    . /tmp/uconf
    echo Building $CONFIG_DEFAULT_DEVICE_TREE
    echo "   $conf"
    rm u-boot-sunxi-with-spl.bin >/dev/null 2>&1
    make $(basename $conf) && make -j 4 && cp -vf u-boot-sunxi-with-spl.bin ../ub/$CONFIG_DEFAULT_DEVICE_TREE
done
