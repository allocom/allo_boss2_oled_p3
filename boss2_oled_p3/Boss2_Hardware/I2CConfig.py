#!/usr/bin/env python3
#
#
#   Enable I2C on P1 and P5 (Rev 2 boards only)
# #######
import os
import mmap
import struct

def get_dt_ranges(filename, offset):
	f = open(filename , "rb")
	f.seek(offset,1)
	data = f.read(4)
	buf = struct.unpack('BBBB', data)
	address = buf[0]<<24 | buf[1]<<16 | buf[2]<<8 | buf[3]<<0
	f.close()
	return address

def bcm_host_get_peripheral_address():
	addr = get_dt_ranges("/proc/device-tree/soc/ranges", 4)
	if addr == 0:
		addr = get_dt_ranges("/proc/device-tree/soc/ranges", 8)
	if addr == 0:
		return 0x20000000
	else:
		return addr

BCM2708_PERI_BASE = bcm_host_get_peripheral_address()

GPIO_BASE=(BCM2708_PERI_BASE + 0x00200000)
BLOCK_SIZE=4096

def _strto32bit_(str):
	return ((str[3])<<24) + ((str[2])<<16) + ((str[1])<<8) + ((str[0]))

def _32bittostr_(val):
	val1 = bytes((chr(val&0xff) + chr((val>>8)&0xff) + chr((val>>16)&0xff) + chr((val>>24)&0xff)), encoding='UTF-8')
	return val1

def get_revision():
	with open('/proc/cpuinfo') as lines:
		for line in lines:
			if line.startswith('Revision'):
				return int(line.strip()[-4:],16)
	raise RuntimeError('No revision found.')

def i2cConfig():
	if get_revision() <= 3:
		print("Rev 2 or greater Raspberry Pi required.")
		return
	# Use /dev/mem to gain access to peripheral registers
	mf=os.open("/dev/mem", os.O_RDWR|os.O_SYNC)
	m = mmap.mmap(mf,BLOCK_SIZE, mmap.MAP_SHARED,
		mmap.PROT_READ|mmap.PROT_WRITE,offset=GPIO_BASE)
	# can close the file after we have mmap
	os.close(mf)
	# Read function select registers
	# GPFSEL0 -- GPIO 0,1 I2C0   GPIO 2,3 I2C1
	m.seek(0)
	reg0=_strto32bit_(m.read(4))
	# GPFSEL2 -- GPIO 28,29 I2C0
	m.seek(8)
	reg2=_strto32bit_(m.read(4))
	m0 = 0b00000000000000000000111111111111
	s0 = 0b00000000000000000000100100000000
	b0 = reg0 & m0
	if b0 != s0:
		print("reg0 I2C configuration not correct. Updating.")
		reg0 = (reg0 & ~m0) | s0
		m.seek(0)
		m.write(_32bittostr_(reg0))

	# GPFSEL2 bits --> x[2] SCL0[3] SDA0[3] x[24]
	#m2 = 0b00111111000000000000000000000000
	#s2 = 0b00100100000000000000000000000000
	#b2 = reg2 & m2
	#print("CONTINUE ************************8")
	#if b2 != s2:
	#    print( "reg2 I2C configuration not correct. Updating.")
	#    reg2 = (reg2 & ~m2) | s2
	#    m.seek(8)
	#    m.write(_32bittostr_(reg2))

	m.close()
