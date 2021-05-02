#!/usr/bin/env python3
"""IRModuleExample1, program to practice using the IRModule

Created July 30, 2020"""

"""
Copyright 2020 allo.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import RPi.GPIO as GPIO
import time
import threading
import subprocess
if os.name != 'posix':
	sys.exit('platform not supported')
import socket
import fcntl
import struct
from datetime import datetime
from threading import Thread
from Hardware.SH1106.SH1106LCD import *
from Hardware.SH1106.SH1106FontLib import *
from Hardware.I2CConfig import *
import IRModule

BASEDIR = os.path.dirname(os.path.abspath(__file__))
PCPIMG = BASEDIR + '/pcp.bmp'

irPin = 16
sw1 = 14
sw2 = 15
sw3 = 23
sw4 = 8
sw5 = 24
rst = 12
#irPin = 36
#sw1 = 8
#sw2 = 10
#sw3 = 16
#sw4 = 24
#sw5 = 18
#rst = 32

h_name = "Allo"
h_ip = ""
w_ip = ""
a_card = "Boss2"
a_card1 = "BOSS2"
indx = 0
m_indx = 1
f_indx = 1
scr_num = 0
alsa_vol = 10
alsa_hvol = 230
alsa_cvol = 230
fil_sp = 0
de_emp = 0
non_os = 0
ph_comp = 0
hv_en = 0
hp_fil = 0
ok_flag = 0
card_num = 0
bit_rate = 0
bit_format = 0
last_bit_format = 0
filter_status = 0
de_ctrl = 'PCM De-emphasis Filter'
hp_ctrl = 'PCM High-pass Filter'
ph_ctrl = 'PCM Phase Compensation'
non_ctrl = 'PCM Nonoversample Emulate'
hv_ctrl = 'HV_Enable'
sp_ctrl = 'PCM Filter Speed'
ma_ctrl = 'Master'
dig_ctrl = 'Digital'
mixerCtrl = ''
mute = 1
sec_flag = 0
status_M = 0
update_M = 0
filter_cur = 0
filter_mod = 0
bs1 = 0
bs2 = 0
bs3 = 0
bs4 = 0
bs5 = 0
irp = 0
irm = 0
ir1 = 0
irok = 0
ir3 = 0
ir4 = 0
ir5 = 0
led_off_counter = 0

lcd = SH1106LCD()

def remote_callback(code):
	global irp
	global irm
	global ir1
	global irok
	global ir3
	global ir4
	global ir5
	global led_off_counter
	if code == 0xC77807F:
		irp = 1
		led_off_counter = 0
	elif code == 0xC7740BF:
		irm = 1
		led_off_counter = 0
	elif code == 0xC77906F:
		ir1 = 1
		led_off_counter = 0
	elif code == 0xC7730CF:
		irok = 1
		led_off_counter = 0
	elif code == 0xC7720DF:
		ir3 = 1
		led_off_counter = 0
	elif code == 0xC77A05F:
		ir4 = 1
		led_off_counter = 0
	elif code == 0xC7710EF:
		ir5 = 1
		led_off_counter = 0
	return


def bootScr():
	global scr_num
	global a_card
	global a_card1
	global h_ip
	global w_ip
	if scr_num != 2:
		scr_num = 2
		lcd.clearScreen()
	lcd.clearScreen()
	h_ip = network1('eth0')
	w_ip = network1('wlan0')
	lcd.displayString(a_card1, 0, 0)
	lcd.displayStringNumber(h_ip, 2, 0)
	lcd.displayString(h_name, 4, 0)
	lcd.displayStringNumber(w_ip, 6, 0)


def infoScr():
	global scr_num
	if scr_num != 0:
		scr_num = 0
		lcd.clearScreen()

	lcd.displayString("VOL", 1, 0)
	lcd.displayString("0.0dB", 1, 60)
	lcd.displayString("PCM/DSD", 3, 0)
	lcd.displayString("SR", 5, 0)
	lcd.displayString("44.1kHz", 5, 60)

def volTimer() :
	global sec_flag
	while 1 :
		time.sleep(1)
		sec_flag = 1

def screenVol():
		global scr_num
		global alsa_vol
		global alsa_hvol
		global alsa_cvol
		global mute
		global ma_ctrl
		global status_M
		if scr_num != 0 :
			scr_num = 0
			lcd.clearScreen()
		if scr_num == 0:
			vol_list = getVol()
			alsa_vol = vol_list[0]
			if vol_list[2] == 0.0 :
				lcd.displayString("    ", 1, 80)
			elif vol_list[2] > -10.0 :
				lcd.displayString("    ", 1, 90)
			elif vol_list[2] > -100.0 :
				lcd.displayString("  ", 1, 100)
			lcd.displayString(alsa_vol, 1, 20)
			getMuteStatus(ma_ctrl)
			mute = status_M
			if mute == 0 :
				lcd.displayString("@", 3, 50)
			else :
				lcd.displayString("  ", 3, 50)
			getHwparam()

def getCardNumber():
		global a_card
		setflag=0
		i = 0
		out = subprocess.Popen(['aplay', '-l'],
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT)
		stdout,stderr = out.communicate()
		line_str = stdout.split(b'\n')
		for line in line_str:
			line = line.decode('utf-8')
			if(a_card in line):
				setflag=1
				word_str = line.split()
				card = word_str[1]
				card_number=(card[0])
				break
		if setflag == 0 :
			print("No Boss2")
			return None
		else :
			return card_number

def getMuteStatus(mixerCtrl):
		global card_num
		global status_M
		cmd = "amixer -c "+ card_num +" get '"+ mixerCtrl +"' | grep off"
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()
		if ( out.decode('utf-8') != "" ):
			status_M = 0
		else:
			status_M = 1

def setMuteStatus(mixerCtrl):
		global card_num
		global update_M
		if ( update_M == 0 ):
			process = subprocess.Popen(["amixer","-c", card_num ,"set",mixerCtrl,"mute"], stdout=subprocess.PIPE, universal_newlines=True)
			stdout,stderr = process.communicate()
		else:
			process = subprocess.Popen(["amixer","-c", card_num ,"set",mixerCtrl,"unmute"], stdout=subprocess.PIPE, universal_newlines=True)
			stdout,stderr = process.communicate()

def getFilterStatus():
		global card_num
		global filter_cur
		cmd = "amixer -c "+ card_num +" get 'PCM Filter Speed' | grep Item0 "
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()
		word_str = out.split()
		current_status = word_str[1]
		#print (current_status.decode('utf-8'))
		if(current_status.decode('utf-8') == "'Slow'"):
			filter_cur = 0
		else:
			filter_cur = 1

def setFilterStatus():
		global card_num
		global filter_mod
		global filter_cur
		if( filter_mod == 0 ):
			cmd = "amixer -c "+ card_num +" set 'PCM Filter Speed' Slow"
		else:
			cmd = "amixer -c "+ card_num +" set 'PCM Filter Speed' Fast"
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()


def getVol():
	global alsa_cvol
	global card_num
	CARD_NUMBER = card_num
	MIXER_CONTROL = 'Master'
	left_dB_val='[-127.50dB]'
	left_hrdware_val=0
	left_percentage_val='[0%]'
	right_dB_val='[-127.50dB]'
	right_hrdware_val=0
	right_percentage_val='[0%]'
	process = subprocess.Popen(["amixer","-c",CARD_NUMBER,"get",MIXER_CONTROL], stdout=subprocess.PIPE, universal_newlines=True)
	stdout,stderr = process.communicate()
	if (stderr == None):
		line_str = stdout.split('\n')
		for line in line_str:
			if('Front Left:' in line):
				word_str = line.split()
				left_hrdware_val=word_str[3]
				left_percentage_val=word_str[4]
				left_dB_val=word_str[5]
			if('Front Right:' in line):
				word_str = line.split()
				right_hrdware_val=word_str[3]
				right_percentage_val=word_str[4]
				right_dB_val=word_str[5]

	left_dB_val = left_dB_val.replace('[', '')
	left_dB_val = left_dB_val.replace(']', '')
	left_dB_list = left_dB_val.split("dB")
	left_dB_val_float = float(left_dB_list[0])
	alsa_cvol = int(left_hrdware_val)
	return [left_dB_val , left_hrdware_val ,left_dB_val_float]

def setVol():
	global alsa_hvol
	global alsa_cvol
	global card_num
	CARD_NUMBER = card_num
	MIXER_CONTROL = 'Master'
	MIXER_CONTROL1 = 'Digital'

	getVol()
	setflag = 0
	if ( alsa_cvol == alsa_hvol):
		setflag = 1
	elif ( alsa_hvol < 0 or alsa_hvol > 255 ):
		setflag = 1
	else:
		cmd = "amixer -c "+ CARD_NUMBER +" set "+ MIXER_CONTROL +" {left},{right}".format(left=alsa_hvol, right=alsa_hvol)
		cmd1 = "amixer -c "+ CARD_NUMBER +" set "+ MIXER_CONTROL1 +" {left},{right}".format(left=alsa_hvol, right=alsa_hvol)
		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()
		proc = subprocess.Popen(cmd1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()

	return setflag

def getHwparam():
	global a_card
	global a_card1
	global card_num
	global bit_rate
	global bit_format
	global last_bit_format
	global led_off_counter
	CARD_NUMBER = card_num
	hw_format = ''
	hw_rate_num = ''
	if ( CARD_NUMBER == -1 ):
		hw_param_out = "No "+ a_card1
	else:
		hw_cmd = "/proc/asound/card"+ str(CARD_NUMBER) +"/pcm0p/sub0/hw_params"
		out = subprocess.Popen(["cat",hw_cmd],
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT)
		stdout,stderr = out.communicate()
		hw_param_str = stdout.rstrip().splitlines()
		if ( hw_param_str[0].decode('utf-8') == 'closed'):
			hw_param_out = 'closed'
		else:
			for line in hw_param_str:
				line = line.decode('utf-8')
				if(line.startswith('format:')):
					format_val = line.split(':')
					hw_format = format_val[1].strip()
				if str(line).find('rate:') != -1:
					rate_val = line.split(':')
					hw_rate = rate_val[1].strip()
					hw_rate_line = hw_rate.split()
					hw_rate_num = int(hw_rate_line[0])
			hw_param_out = [hw_format , hw_rate_num]
	if hw_format == "S24_LE" :
		bit_rate = '24'
		bit_format = hw_rate_num
		bit_format1 = str(bit_format)
		lcd.displayString(bit_rate, 5, 15)
		lcd.displayString("S", 5, 5)
		if(last_bit_format != bit_format1):
			lcd.displayString("        ", 5, 50)
			last_bit_format = bit_format1
		lcd.displayString(bit_format1, 5, 50)
		led_off_counter = 0
	elif hw_format == "S32_LE" :
		bit_rate = '32'
		bit_format = hw_rate_num
		bit_format1 = str(bit_format)
		lcd.displayString(bit_rate, 5, 15)
		lcd.displayString("S", 5, 5)
		if(last_bit_format != bit_format1):
			lcd.displayString("        ", 5, 50)
			last_bit_format = bit_format1
		lcd.displayString(bit_format1, 5, 50)
		led_off_counter = 0
	elif hw_format == "S16_LE" :
		bit_rate = '16'
		bit_format = hw_rate_num
		bit_format1 = str(bit_format)
		lcd.displayString(bit_rate, 5, 15)
		lcd.displayString("S", 5, 5)
		if(last_bit_format != bit_format1):
			lcd.displayString("        ", 5, 50)
			last_bit_format = bit_format1
		lcd.displayString(bit_format1, 5, 50)
		led_off_counter = 0
	else :
		bit_rate = "closed"
		lcd.displayStringNumber("   ", 5, 15)
		lcd.displayString(" ", 5, 5)
		lcd.displayString("        ", 5, 50)
		last_bit_format = 0


def menuScr():
		global scr_num
		global m_indx
		if scr_num != 1:
			scr_num = 1
			lcd.clearScreen()
		if m_indx == 1 :
			lcd.displayInvertedString("SYSINFO", 0, 0)
		else:
			lcd.displayString("SYSINFO", 0, 0)
		if m_indx == 2 :
			if hv_en == 0 :
				lcd.displayInvertedString("HV-EN OFF", 2, 0)
			else :
				lcd.displayInvertedString("HV-EN ON", 2, 0)
		else:
			if hv_en == 0 :
				lcd.displayString("HV-EN OFF", 2, 0)
			else :
				lcd.displayString("HV-EN ON", 2, 0)
		if m_indx == 3 :
			lcd.displayInvertedString("FILTER", 4, 0)
		else:
			lcd.displayString("FILTER", 4, 0)
		if m_indx == 4 :
			if fil_sp == 1 :
				lcd.displayInvertedString("F-SPEED-FAS", 6, 0)
			else :
				lcd.displayInvertedString("F-SPEED-SLO", 6, 0)
		else :
			if fil_sp == 1 :
				lcd.displayString("F-SPEED-FAS", 6, 0)
			else :
				lcd.displayString("F-SPEED-SLO", 6, 0)


def filtScr():
	global scr_num
	global fil_sp
	global hp_fil
	global de_emp
	global non_os
	global ph_comp
	global f_indx
	if scr_num != 3 :
		scr_num = 3
		lcd.clearScreen()
	if f_indx == 1 :
		lcd.displayInvertedString("PHCOMP ", 0, 5)
		lcd.displayInvertedString("| ",0, 64)
		if ph_comp == 0 :
			lcd.displayInvertedString("DIS", 0, 80)
		else :
			lcd.displayInvertedString("EN", 0, 80)
	else:
		lcd.displayString("PHCOMP ", 0, 5)
		lcd.displayString("| ",0, 64)
		if ph_comp== 0 :
			lcd.displayString("DIS", 0, 80)
		else :
			lcd.displayString("EN", 0, 80)

	if f_indx == 2 :
		lcd.displayInvertedString("HP-FIL ", 2, 5)
		lcd.displayInvertedString("| ",2, 64)
		if hp_fil == 0 :
			 lcd.displayInvertedString("DIS", 2, 80)
		else :
			lcd.displayInvertedString("EN", 2, 80)
	else:
		lcd.displayString("HP-FIL ", 2, 5)
		lcd.displayString("| ",2, 64)
		if hp_fil == 0 :
			lcd.displayString("DIS", 2, 80)
		else :
			lcd.displayString("EN", 2, 80)
	if f_indx == 3 :
		lcd.displayInvertedString("DE-EMP ", 4, 5)
		lcd.displayInvertedString("| ",4, 64)
		if de_emp == 0 :
			lcd.displayInvertedString("DIS", 4, 80)
		else :
			lcd.displayInvertedString("EN", 4, 80)
	else:
		lcd.displayString("DE-EMP ", 4, 5)
		lcd.displayString("| ",4, 64)
		if  de_emp == 0 :
			lcd.displayString("DIS", 4, 80)
		else :
			lcd.displayString("EN", 4, 80)
	if f_indx == 4 :
		lcd.displayInvertedString("NON-OS ", 6, 5)
		lcd.displayInvertedString("| ",6, 64)
		if non_os == 0 :
			lcd.displayInvertedString("DIS", 6, 80)
		else :
			lcd.displayInvertedString("EN", 6, 80)
	else :
		lcd.displayString("NON-OS ", 6, 5)
		lcd.displayString("| ",6, 64)
		if non_os == 0 :
			lcd.displayString("DIS", 6, 80)
		else :
			lcd.displayString("EN", 6, 80)

def spScr5():
	global scr_num
	global fil_sp
	global ok_flag
	if scr_num != 5 :
		scr_num = 5
		lcd.clearScreen()
	lcd.displayString("FILTER SPEED", 0, 5)
	if fil_sp == 0 :
		lcd.displayString("FAST", 3, 10)
		lcd.displayInvertedString("SLOW", 3, 80)
	else :
		lcd.displayInvertedString("FAST", 3, 10)
		lcd.displayString("SLOW", 3, 80)
	if ok_flag == 1 :
		lcd.displayInvertedString("OK", 6, 50)
	else :
		lcd.displayString("OK", 6, 50)

def hpScr6():
	global scr_num
	global ok_flag
	global hp_fil
	if scr_num != 6 :
		scr_num = 6
		lcd.clearScreen()
	lcd.displayString("HP-FILT", 0, 20)
	if hp_fil == 0 :
		lcd.displayString("EN", 3, 10)
		lcd.displayInvertedString("DIS", 3, 70)
	else :
		lcd.displayInvertedString("EN", 3, 10)
		lcd.displayString("DIS", 3, 70)
	if ok_flag == 1 :
		lcd.displayInvertedString("OK", 6, 50)
	else :
		lcd.displayString("OK", 6, 50)

def deScr7():
	global scr_num
	global de_emp
	global ok_flag
	if scr_num != 7 :
		scr_num = 7
		lcd.clearScreen()
	lcd.displayString("DE-EMPH", 0, 20)
	if de_emp == 0 :
		lcd.displayString("EN", 3, 10)
		lcd.displayInvertedString("DIS", 3, 70)
	else :
		lcd.displayInvertedString("EN", 3, 10)
		lcd.displayString("DIS", 3, 70)
	if ok_flag == 1 :
		lcd.displayInvertedString("OK", 6, 50)
	else :
		lcd.displayString("OK", 6, 50)


def nonScr8():
	global scr_num
	global non_os
	global ok_flag
	if scr_num != 8 :
		scr_num = 8
		lcd.clearScreen()
	lcd.displayString("NON-OSAMP", 0, 20)
	if non_os == 0 :
		lcd.displayString("EN", 3, 10)
		lcd.displayInvertedString("DIS", 3, 70)
	else :
		lcd.displayInvertedString("EN", 3, 10)
		lcd.displayString("DIS", 3, 70)
	if ok_flag == 1 :
		lcd.displayInvertedString("OK", 6, 50)
	else :
		lcd.displayString("OK", 6, 50)

def phScr9():
	global scr_num
	global ph_comp
	global ok_flag
	if scr_num != 9 :
		scr_num = 9
		lcd.clearScreen()
	lcd.displayString("PHA-COMP", 0, 20)
	if ph_comp == 0 :
		lcd.displayString("EN", 3, 10)
		lcd.displayInvertedString("DIS", 3, 70)
	else :
		lcd.displayInvertedString("EN", 3, 10)
		lcd.displayString("DIS", 3, 70)
	if ok_flag == 1 :
		lcd.displayInvertedString("OK", 6, 50)
	else :
		lcd.displayString("OK", 6, 50)

def hvScr4():
	global scr_num
	global hv_en
	global ok_flag
	if scr_num != 4 :
		scr_num = 4
		lcd.clearScreen()
	lcd.displayString("HV ENABLE", 0, 20)
	if hv_en == 0 :
		lcd.displayString("ON", 3, 20)
		lcd.displayInvertedString("OFF", 3, 70)
	else :
		lcd.displayInvertedString("ON", 3, 20)
		lcd.displayString("OFF", 3, 70)
	if ok_flag == 1 :
		lcd.displayInvertedString("OK", 6, 50)
	else :
		lcd.displayString("OK", 6, 50)


def network1(ifname):
	ip_address = '';
	global w_ip
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		ip_address = socket.inet_ntoa(fcntl.ioctl(
			s.fileno(),
			0x8915,
			struct.pack('256s', bytes(ifname[:15], 'utf-8'))
		)[20:24])
	except :
		ip_address = ''

	return ip_address


def init_gpio():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(sw1, GPIO.IN)
	GPIO.setup(sw2, GPIO.IN)
	GPIO.setup(sw3, GPIO.IN)
	GPIO.setup(sw4, GPIO.IN)
	GPIO.setup(sw5, GPIO.IN)
	GPIO.setup(irPin,GPIO.IN)
	time.sleep(0.1)

def init_gpio_bcm():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(sw1, GPIO.IN)
	GPIO.setup(sw2, GPIO.IN)
	GPIO.setup(sw3, GPIO.IN)
	GPIO.setup(sw4, GPIO.IN)
	GPIO.setup(sw5, GPIO.IN)
	GPIO.setup(irPin,GPIO.IN)
	time.sleep(0.1)

def main(IRenabled):
	global m_indx
	global h_ip
	global w_ip
	global h_name
	global scr_num
	global alsa_vol
	global alsa_hvol
	global alsa_cvol
	global f_indx
	global fil_sp
	global hp_fil
	global de_emp
	global ph_comp
	global non_os
	global hv_en
	global ok_flag
	global card_num
	global de_ctrl
	global hp_ctrl
	global hv_ctrl
	global non_ctrl
	global ma_ctrl
	global dig_ctrl
	global ph_ctrl
	global mixerCtrl
	global status_M
	global update_M
	global filter_cur
	global filter_mod
	global mute
	global sec_flag
	global bs1
	global bs2
	global bs3
	global bs4
	global bs5
	global irm
	global irok
	global ir1
	global ir3
	global ir4
	global ir5
	global led_off_counter
	LED_FLAG = 0
	led_off_counter = 1
	i2cConfig()
	lcd = SH1106LCD()
	
	try:
		f = open(PCPIMG, 'r')
		if f is not None:
			f.close()
			lcd.displayImage(PCPIMG, 0, 0)
			time.sleep(5)
			lcd.clearScreen()
	except:
		print("Error opening " + PCPIMG)

	h_ip = network1('eth0')
	w_ip = network1('wlan0')
	if h_ip != '':
		lcd.displayStringNumber(h_ip,0,0)
	if w_ip != '':
		lcd.displayStringNumber(w_ip,6,0)
	h_name = "HOST:%s" % socket.gethostname()
	lcd.displayString(h_name,2,0)
	lcd.displayString(a_card1,4,0)
	time.sleep(5)
	lcd.clearScreen()
	card_num1 = getCardNumber()
	if card_num1 == None :
		print("no card detected")
		lcd.displayString("NO BOSS2", 4, 5)
		lcd.displayStringNumber(h_ip,0,0)
		lcd.displayStringNumber(w_ip,6,0)
		exit(0)

	time.sleep(0.04)
	init_gpio_bcm()
	scr0_ref_count = 0
	card_num = getCardNumber()
	timer1 = time.time()
	timerButton1 = time.time()

	if IRenabled:
		ir = IRModule.IRRemote(callback='DECODE')
		GPIO.add_event_detect(irPin,GPIO.BOTH,callback=ir.pWidth)
		ir.set_callback(remote_callback)

#    try :
	screenVol()
	getMuteStatus(ma_ctrl)
	mute = status_M
	getMuteStatus(hp_ctrl)
	hp_fil = status_M
	getMuteStatus(hv_ctrl)
	hv_en = status_M
	getMuteStatus(non_ctrl)
	non_os = status_M
	getMuteStatus(ph_ctrl)
	ph_comp = status_M
	getMuteStatus(de_ctrl)
	de_emp = status_M
	getFilterStatus()
	fil_sp = filter_cur
	while 1:
		if led_off_counter == 950:
			LED_FLAG = 1
		elif led_off_counter == 1 :
			LED_FLAG = 0
		if led_off_counter > 950:
			led_off_counter = 951
		if LED_FLAG == 1:
			lcd.powerDown()
			LED_FLAG = 2
		elif LED_FLAG == 0:
			lcd.powerUp()
			LED_FLAG = 2
		if scr0_ref_count <  10 :
			scr0_ref_count += 1
			time.sleep(0.02)
		else :
			sec_flag = 1
			scr0_ref_count = 0
		if(GPIO.input(sw1) == GPIO.HIGH):
			time.sleep(0.04)
		else :
			time.sleep(0.04)
			bs1 = 1
			led_off_counter = 0
		if(GPIO.input(sw2) == GPIO.HIGH):
			time.sleep(0.04)
		else :
			time.sleep(0.04)
			bs2 = 1
			led_off_counter = 0
		if(GPIO.input(sw3) == GPIO.HIGH):
			time.sleep(0.04)
		else :
			time.sleep(0.04)
			bs3 = 1
			led_off_counter = 0
		if(GPIO.input(sw4) == GPIO.HIGH):
			time.sleep(0.04)
		else :
			time.sleep(0.04)
			bs4 = 1
			led_off_counter = 0
		if(GPIO.input(sw5) == GPIO.HIGH):
			time.sleep(0.04)
		else :
			time.sleep(0.04)
			bs5 = 1
			led_off_counter = 0
		if bs1 == 1 or ir1 == 1:
			time.sleep(0.1)
			bs1 = 0
			ir1 = 0
			if scr_num == 0 :
				lcd.clearScreen()
				menuScr()
			elif scr_num == 1:
				screenVol()
			elif scr_num == 2 :
				menuScr()
			elif scr_num == 3 :
				menuScr()
			elif scr_num == 4 :
				if hv_en == 0 :
					hv_en = 1
					hvScr4()
			elif scr_num == 5 :
				if fil_sp == 0 :
					fil_sp = 1
					spScr5()
			elif scr_num == 6 :
				if hp_fil == 0 :
					hp_fil = 1
					hpScr6()
			elif scr_num == 7 :
				if de_emp == 0 :
					de_emp = 1
					deScr7()
			elif scr_num == 8 :
				if non_os == 0 :
					non_os = 1
					nonScr8()
			elif scr_num == 9 :
				if ph_comp == 0 :
					ph_comp = 1
					phScr9()
			else :
				print(scr_num)

		if irm == 1 :
			time.sleep(0.1)
			sec_flag = 1
			irm = 0
			getMuteStatus(ma_ctrl)
			mute = status_M
			if mute == 0 :
				update_M = 1
				setMuteStatus(ma_ctrl)
				setMuteStatus(dig_ctrl)
			else :
				update_M = 0
				setMuteStatus(ma_ctrl)
				setMuteStatus(dig_ctrl)

		if bs2 == 1 or irok == 1 :
			time.sleep(0.1)
			bs2 = 0
			irm_nflag = 0
			if irok ==  1 :
				irm_nflag = 1
				irok = 0
			if scr_num == 0 and irm_nflag == 0 :
				sec_flag = 1
				getMuteStatus(ma_ctrl)
				mute = status_M
				if mute == 0 :
					update_M = 1
					setMuteStatus(ma_ctrl)
					setMuteStatus(dig_ctrl)
				else :
					update_M = 0
					setMuteStatus(ma_ctrl)
					setMuteStatus(dig_ctrl)
			elif scr_num == 1 :
				if m_indx == 1 :
					bootScr()
				elif m_indx == 2 :
					hvScr4()
				elif m_indx == 3 :
					filtScr()
				elif m_indx == 4 :
					spScr5()
			elif scr_num == 2 :
				menuScr()
			elif scr_num == 3:
				if f_indx == 1 :
					phScr9()
				elif f_indx == 2 :
					hpScr6()
				elif f_indx == 3 :
					deScr7()
				elif f_indx == 4 :
					nonScr8()
			elif scr_num == 4:
					ok_flag = 0
					getMuteStatus(hv_ctrl)
					if status_M != hv_en :
						update_M = hv_en
						setMuteStatus(hv_ctrl)
					menuScr()
			elif scr_num == 5:
					ok_flag = 0
					getFilterStatus()
					if filter_cur != fil_sp :
						filter_mod = fil_sp
						setFilterStatus()
					menuScr()
			elif scr_num == 6:
					ok_flag = 0
					getMuteStatus(hp_ctrl)
					if status_M != hp_fil :
						update_M = hp_fil
						setMuteStatus(hp_ctrl)
					filtScr()
			elif scr_num == 7:
					ok_flag = 0
					getMuteStatus(de_ctrl)
					if status_M != de_emp :
						update_M = de_emp
						setMuteStatus(de_ctrl)
					filtScr()
			elif scr_num == 8:
					ok_flag = 0
					getMuteStatus(non_ctrl)
					if status_M != non_os :
						update_M = non_os
						setMuteStatus(non_ctrl)
					filtScr()
			elif scr_num == 9:
					ok_flag = 0
					getMuteStatus(ph_ctrl)
					if status_M != ph_comp :
						update_M = ph_comp
						setMuteStatus(ph_ctrl)
					filtScr()

		if bs3 == 1 or ir3 == 1:
			time.sleep(0.1)
			bs3 = 0
			ir3 = 0
			if scr_num == 0 :
				getVol()
				alsa_hvol = alsa_cvol
				if alsa_hvol < 255 and alsa_hvol >= 240 :
					alsa_hvol += 1
				if  alsa_hvol < 240 and alsa_hvol >= 210 :
					alsa_hvol += 3
				if  alsa_hvol < 210 and alsa_hvol >= 120 :
					alsa_hvol += 10
				if alsa_hvol < 120 and alsa_hvol >= 0 :
					alsa_hvol += 30
				setVol()
				screenVol()
			elif scr_num == 1 :
				if  m_indx > 1 :
					m_indx -= 1
				menuScr()
			elif scr_num == 3 :
				if f_indx > 1 :
					f_indx -= 1
				filtScr()

		if bs4 == 1 or ir4 == 1:
			time.sleep(0.1)
			bs4 = 0
			ir4 = 0
			if scr_num == 0 :
				getVol()
				alsa_hvol = alsa_cvol
				if alsa_hvol <= 255 and alsa_hvol > 240 :
					alsa_hvol -= 1
				if  alsa_hvol <=240 and alsa_hvol > 210 :
					alsa_hvol -= 3
				if  alsa_hvol <= 210 and alsa_hvol > 120 :
					alsa_hvol -= 10
				if alsa_hvol <= 120 and alsa_hvol > 0 :
					alsa_hvol -= 30
				setVol()
				screenVol()

			elif scr_num == 1 :
				m_indx += 1
				if  m_indx > 4 :
					m_indx = 1
				menuScr()
			elif scr_num == 3 :
				f_indx += 1
				if f_indx > 4 :
					f_indx = 1
				filtScr()
			elif scr_num == 4 :
				if ok_flag == 0 :
					ok_flag = 1
				hvScr4()
			elif scr_num == 5 :
				if ok_flag == 0 :
					ok_flag = 1
				spScr5()
			elif scr_num == 6 :
				if ok_flag == 0 :
					ok_flag = 1
				hpScr6()

			elif scr_num == 7 :
				if ok_flag == 0 :
					ok_flag = 1
				deScr7()
			elif scr_num == 8 :
				if ok_flag == 0 :
					ok_flag = 1
				nonScr8()
			elif scr_num == 9 :
				if ok_flag == 0 :
					ok_flag = 1
				phScr9()

		if bs5 == 1 or ir5 == 1:
			time.sleep(0.1)
			bs5 = 0
			ir5 = 0
			if scr_num == 0 :
				lcd.clearScreen()
				menuScr()
			elif scr_num == 1:
				screenVol()
			elif scr_num == 2 :
				menuScr()
			elif scr_num == 3 :
				menuScr()
			elif scr_num == 4 :
				if hv_en == 1 :
					hv_en = 0
				hvScr4()
			elif scr_num == 5 :
				if fil_sp == 1 :
					fil_sp = 0
				spScr5()
			elif scr_num == 6 :
				if hp_fil == 1 :
					hp_fil = 0
				hpScr6()
			elif scr_num == 7 :
				if de_emp == 1 :
					de_emp = 0
				deScr7()
			elif scr_num == 8 :
				if non_os == 1 :
					non_os = 0
				nonScr8()
			elif scr_num == 9 :
				if ph_comp == 1 :
					ph_comp = 0
				phScr9()

		if sec_flag == 1 :
			if scr_num == 0 :
				screenVol()
				sec_flag = 0
		led_off_counter += 1
#    except:
	if IRenabled:
		ir.remove_callback()
		GPIO.cleanup(irPin)
	print ("exit")
	GPIO.cleanup(sw1)
	GPIO.cleanup(sw2)
	GPIO.cleanup(sw3)
	GPIO.cleanup(sw3)
	GPIO.cleanup(sw4)
	GPIO.cleanup(sw5)

def usage():
	print("Usage: %s" % __file__)
	print('       --noir:    Do not use ir remote functionality')
	print('')
	sys.exit(1)


if __name__ == "__main__":
	ir_en = True

	for arg in sys.argv:
		if any( x in arg for x in ["-h", "--help"]):
			usage()
		if '--noir' in arg:
			ir_en = False

	main(ir_en)
