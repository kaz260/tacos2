#!/usr/bin/python
#-*- coding:utf-8 -*-
import tacos2

if __name__ == "__main__":
    instr = tacos2.Instrument("/dev/ttyUSB0")
#    instr.debug = True

    instr.set(0x1, 0x6, 40, 77)

    height, angle = instr.get(0x1)

    print "height:{} angle:{}".format(ord(height), ord(angle))


    instr.set(0x1, 0x6, 30, 40)

    height, angle = instr.get(0x1)

    print "height:{} angle:{}".format(ord(height), ord(angle))

    instr.set(0x1, 0x6, 30, 255)

    height, angle = instr.get(0x1)

    print "height:{} angle:{}".format(ord(height), ord(angle))

    instr.set(0x1, 0x6, 255, 49)

    height, angle = instr.get(0x1)

    print "height:{} angle:{}".format(ord(height), ord(angle))

    instr.set(0x1, 0x6, 255, 255)

    height, angle = instr.get(0x1)

    print "height:{} angle:{}".format(ord(height), ord(angle))

