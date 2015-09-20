cat << EOF |sudo tee /etc/udev/rules.d/99-gendis.rules
# Dexis Platinum
#SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="5328", ATTRS{idProduct}=="2009", RUN+="/sbin/fxload -v -t fx2 -I /usr/share/usb/GendexII_1.hex -s /usr/share/usb/GendexII_2.hex -D $tempnode"
# Gendex GX700
#SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="5328", ATTRS{idProduct}=="202F", RUN+="/sbin/fxload -v -t fx2 -I /usr/share/usb/GendexII_1.hex -s /usr/share/usb/GendexII_2.hex -D $tempnode"




# Dexis Platinum
#SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="5328", ATTRS{idProduct}=="2009", RUN+="touch /tmp/stuff"
# Gendex GX700
#SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="5328", ATTRS{idProduct}=="202F", RUN+="touch  /tmp/stuff"


# Dexis Platinum
ACTION=="add", SUBSYSTEM=="usb_device", SYSFS{idVendor}=="5328", SYSFS{idProduct}=="2009", MODE="0666"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="5328", ATTR{idProduct}=="2009", MODE="0666"

# Gendex GX700
ACTION=="add", SUBSYSTEM=="usb_device", SYSFS{idVendor}=="5328", SYSFS{idProduct}=="202F", MODE="0666"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="5328", ATTR{idProduct}=="202F", MODE="0666"
# After renumeration
ACTION=="add", SUBSYSTEM=="usb_device", SYSFS{idVendor}=="5328", SYSFS{idProduct}=="2030", MODE="0666"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="5328", ATTR{idProduct}=="2030", MODE="0666"
EOF
