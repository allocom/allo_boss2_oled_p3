#!/bin/sh
#piCoreplayer this script execute in webgui tweaks user commands page
sudo modprobe i2c-dev
sudo python3 /opt/boss2_oled_p3/boss2_oled.py &
