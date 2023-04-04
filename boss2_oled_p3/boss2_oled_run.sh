#!/bin/sh
#piCoreplayer this script execute in webgui tweaks user commands page
sudo modprobe i2c-dev
sudo python3 /usr/local/bin/boss2_oled.py &
