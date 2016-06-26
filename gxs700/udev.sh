cat << EOF |sudo tee /etc/udev/rules.d/99-gendis.rules
# Dexis Platinum
# Pre renumeration
ACTION=="add", SUBSYSTEM=="usb_device", SYSFS{idVendor}=="5328", SYSFS{idProduct}=="2009", MODE="0666"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="5328", ATTR{idProduct}=="2009", MODE="0666"
# Post enumeration
# In theory...although I guess I'm loading the same (wrong?) FW for both
ACTION=="add", SUBSYSTEM=="usb_device", SYSFS{idVendor}=="5328", SYSFS{idProduct}=="2010", MODE="0666"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="5328", ATTR{idProduct}=="2010", MODE="0666"

# Gendex GX700
# Pre renumeration
ACTION=="add", SUBSYSTEM=="usb_device", SYSFS{idVendor}=="5328", SYSFS{idProduct}=="202F", MODE="0666"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="5328", ATTR{idProduct}=="202F", MODE="0666"
# Post renumeration
ACTION=="add", SUBSYSTEM=="usb_device", SYSFS{idVendor}=="5328", SYSFS{idProduct}=="2030", MODE="0666"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="5328", ATTR{idProduct}=="2030", MODE="0666"
EOF
