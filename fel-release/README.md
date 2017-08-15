# this is a work in progress only h3droid installation is handled for now
# documentation will be hosted at https://www.hdroid.com/fel/

python3 -u -B h3droid_fel.py
 
  ~~default  is g_mass_storage / g_serial installer~~ 
  now use adb for transport, requires driver install, but no more need for root or uac
  
  
The micropython code part is served to the board through host python3 webdav, it will list  emmc/sdcard/aoe/usbstorage

The OS images images are mounted through webdav+archivefs or exported as block devices with host python3 nbd server


NOTE: python3 support on windows is for MSYS/MINGW version.





#
