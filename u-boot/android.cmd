# mkimage -C none -A arm -T script -d boot.cmd boot.scr
setenv machid 1029
setenv bootm_boot_mode sec


setenv kernel_addr_r    0x41000000
setenv fel_scriptaddr   0x43000000
setenv scriptaddr       0x43100000
setenv ramdisk_addr_r   0x50000000


setenv kernel_addr_r    %kernel_addr_r%
setenv fel_scriptaddr   %fel_scriptaddr%
setenv scriptaddr       %scriptaddr%
setenv ramdisk_addr_r   %ramdisk_addr_r%


# fel defaults:
# dfu_alt_info_ram=kernel ram 0x42000000 0x1000000;fdt ram 0x43000000 0x100000;ramdisk ram 0x43300000 0x4000000
# fel_scriptaddr=43100000 kernel_addr_r=0x42000000 pxefile_addr_r=0x43200000
# ramdisk_addr_r=0x43300000 scriptaddr=0x43100000

# if <list>; then <command list>; [ elif <list>; then <list>; ] ... [ else <list>; ] fi
# while <list> ; do <list> ; done
# until <list> ; do <list> ; done
# for <name> in <word list> ; do <list> ; done

#orig: setenv bootargs "root=/dev/ram0 rw init=/init vmalloc=384M sunxi_fb_mem_reserve=16 earlyprintk=ttyS0,115200"
# disp_para=405


setenv scriptbin "%H3I_FEX%"

if load mmc 0:1 ${fel_scriptaddr} ${scriptbin}
then
    echo "==FEL== MMC0 unit"
    setenv boot_targets mmc0
    setenv MMC "mmcblk0p"
else
    echo "==FEL== MMC1 unit"
    setenv boot_targets mmc1
    setenv MMC "mmcblk1p"
    load mmc 1:1 ${fel_scriptaddr} ${scriptbin}
fi



#setenv bootargs "${bootargs} init_disp=20b0405 tv_vdid=0 fb_base=0x46400000"

setenv bootargs "root=/dev/ram0 rw console=ttyS0,115200 init=/init loglevel=4 rootwait initcall_debug=0 vmalloc=384M sunxi_fb_mem_reserve=16"
setenv bootargs "${bootargs} mac_addr= wifi_mac= bt_mac= specialstr= serialno= boot_type=1 config_size=49152"
setenv bootargs "${bootargs} hdmi.audio=EDID:0 disp.screen0_output_mode=EDID:1280x720p50"
setenv layout "bootloader@${MMC}1:Reserve0@null:private@null"
setenv bootargs "${bootargs} partitions=${layout}:env@${MMC}5:boot@$null:system@null:misc@null:recovery@null:sysrecovery@null:klog@null:cache@null:UDISK@null"

setenv pled "pl10"
setenv aled "pa15"
setenv rkey "pl03"

setenv wifi ""; # wifi=[u|s]:vendor_id:product_id:vendor_name:kernel_module:

# we are ready to boot, light the aled
if test -n "${aled}"
then
    gpio toggle ${aled}
fi

echo
echo "==FEL==  Booting H3droid"
#setenv bootargs "${bootargs} ${wifi}"

# 0x2 0000 == 128kB, 0x10 0000 == 1MB, 0x100 0000 == 16MB

#load mmc 1:1 0x47800000 /h3droid_ramdisk.u
#load mmc 1:1 0x48000000 /h3droid_zImage.u
#bootz 0x42000000 0x43200000

#bootz 0x41000000 0x50000000
bootz ${kernel_addr_r} ${ramdisk_addr_r}
