#!/usr/bin/python
#-*- coding:utf-8 -*-
import tacos2

if __name__ == "__main__":
    instr = tacos2.Instrument("/dev/ttyUSB0")
    instr.debug = True

    while True:
        instr.setSlaveAddress(0x01)
        instr.respond()

