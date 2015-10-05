cat << EOF |sudo tee /etc/udev/rules.d/99-bpm.rules
# Pro 16
ACTION=="add", SUBSYSTEM=="usb_device", SYSFS{idVendor}=="14b9", SYSFS{idProduct}=="0001", MODE="0666"
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="14b9", ATTR{idProduct}=="0001", MODE="0666"
EOF

