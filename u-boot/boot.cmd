setenv bootm_boot_mode sec
setenv machid 1029
#setenv video-mode sunxi:1024x768-24@50,monitor=dvi,hpd=0,edid=
setenv stdout "serial,vga"
setenv stderr "serial,vga"

setenv kernel_addr_r    %kernel_addr_r%
setenv fel_scriptaddr   %fel_scriptaddr%
setenv scriptaddr       %scriptaddr%
setenv ramdisk_addr_r   %ramdisk_addr_r%



setenv root "root=/dev/ram0 rootwait rootfstype=ext4"
# earlyprintk"

setenv consoleargs "consoleblank=0 console=tty1 console=ttyS0,115200"
setenv display "hdmi.audio=EDID:0 disp.screen0_output_mode=EDID:1280x1024p60 no_console_suspend=1"
setenv sunxikw "sunxi_ve_mem_reserve=0 sunxi_g2d_mem_reserve=0 sunxi_fb_mem_reserve=16"

setenv bootargs "XYZ:d41d8cd98f00b204e9800998ecf8427e ${root} ${display} ${sunxikw} ${consoleargs} panic=60 loglevel=1 cgroup_enable=memory swapaccount=1 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

lcdputs (FELInstaller)

echo "========== BOOT LEGACY (XYZ) ===========  ${kernel_addr_r} ${ramdisk_addr_r} ${fdt_addr_r} "
bootz ${kernel_addr_r} ${ramdisk_addr_r}
