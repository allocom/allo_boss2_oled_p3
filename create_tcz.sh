#!/bin/sh

EXTNAM="allo-boss2"
TMPDIR="/tmp/$EXTNAM"

mkdir -p $TMPDIR/usr/local/bin
mkdir -p $TMPDIR/usr/local/lib/python3.8/site-packages
mkdir -p $TMPDIR/usr/local/share/allo-boss2

cd boss2_oled_p3

cp -avr Boss2_Hardware $TMPDIR/usr/local/lib/python3.8/site-packages/
cp boss2_oled* $TMPDIR/usr/local/bin
cp pcp.bmp $TMPDIR/usr/local/share/allo-boss2
cp README $TMPDIR/usr/local/share/allo-boss2

cd $TMPDIR
find * -not -type d > ../$EXTNAM.tcz.list
cd ..
mksquashfs $EXTNAM $EXTNAM.tcz -noappend
md5sum $EXTNAM.tcz > $EXTNAM.tcz.md5.txt
