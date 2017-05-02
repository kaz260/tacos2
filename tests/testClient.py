#!/usr/bin/python
#-*- coding:utf-8 -*-
import tacos2
import dummy_serial

if __name__ == "__main__":

    tacos2.serial.Serial = dummy_serial.Serial
    instr = tacos2.Instrument('DUMMYPORTNAME')
    instr.debug = True

    instr.setSlaveAddress(0x01)
    instr.respond()

