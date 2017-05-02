#!/usr/bin/python
#-*- coding:utf-8 -*-
import tacos2
import pseudoSerial

if __name__ == "__main__":

    tacos2.serial.Serial = pseudoSerial.Serial
    instr = tacos2.Instrument('dummy')
    instr.debug = True

    print instr.get(0x1)

    instr.set(0x1, 0x6, 50, 80)

    instr.stop(0x1, 0x6)
