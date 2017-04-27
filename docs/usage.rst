.. _usage:

========
Usage
========

General on Tacos2 protocol
--------------------------
Tacos2 is a serial communications protocol published by Tachikawa Blind.
It is dedicated protocol for Tachikawa Blind.


Typical hardware
----------------
Tacos2 works with RS-485 serial communication protocol.
Detail of th Tacos2 is descrved below:

Communication Method: RS-485
Baudrate: 9600bps
Startbit: 1bit
Stopbit: 1bit
Encoding: 8bit
Parity: None
ErrorDetection: FCC(1 byte)

Frame format

| DLE+STX | BC | DAS | DAE | CW | SAX | SA | data(variable length) | DLE+EXT | FCC |
DLE: 0x10
STX: 0x02
ETX: 0x03
BC: byte count from DAS to EXT
DAS: Destination Address Start
DAE: Distination Address End
SA: Source Address
CW: Control Word
	bit7:  1:command field only 0:command with data
	bit6:  1:command 0:response
	bit5:  1:auto 0:local
	bit4~0: reserved (must be 0)
FCC: Frame Check Code. Two's complement of sum of BC to ETX

Caution:
If DAS, DAE and data contain 0x10, escape character 0x10 must be added right before.


Typical usage
-------------
The instrument is typically connected via a serial port, and a USB-to-serial 
adaptor should be used on most modern computers. How to configure such a serial 
port is described on the pySerial page: http://pyserial.sourceforge.net/

For example, address number 1 to which we are to communicate via a serial port with the name 
``/dev/ttyUSB1``. The instrument stores the measured temperature in register 289. 
For this instrument a temperature of 77.2 C is stored as (the integer) 772, 
why we use 1 decimal. To read this data from the instrument::

    #!/usr/bin/env python
    import tacos2

    instrument = tacos2.Instrument('/dev/ttyUSB1', 0xC0) # port name, master address

    ## Set Blind height ##
    instrument.set(1, 6, hight=10) # DAS, DAE and height in percentage.

    ## Set Slat angle ##
    instrument.set(1, 6, angle=20) # DAS, DAE and height in percentage.

    ## Set both heigth and angle ##
    instrument.set(1, 6, height=10, angle=20) 

    ## stop #
    instrument.stop()

The full API for Tacos2 is available in :ref:`apitacos2`.


Default values
--------------
Most of the serial port parameters have the default values(9600 8N1)::

    instrument.serial.port          	# this is the serial port name
    instrument.serial.baudrate = 9600   # Baudrate
    instrument.serial.bytesize = 8
    instrument.serial.parity   = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout  = 0.05   # seconds

    instrument.sa     			# this is the master address number

These can be overridden::
    
    instrument.serial.timeout = 0.2
    
To see which settings you actually are using::

    print instrument     

For details on the allowed parity values, see http://pyserial.sourceforge.net/pyserial_api.html#constants 

To change the parity setting, use::

    import serial
    instrument.serial.parity = serial.PARITY_EVEN

or alternatively (to avoid import of ``serial``)::

    instrument.serial.parity = tacos2.serial.PARITY_EVEN


Handling communication errors
-----------------------------
Your top-level code should be able to handle communication errors. This is typically done with try-except. 

Instead of running::

    print(instrument.set(1, 6, height=20))

Use::
 
    try:
        print(instrument.set(1, 6, height=20))
    except IOError:
        print("Failed to set instrument")

Different types of errors should be handled separately.

