==============
Tacos2 details
==============

Tacos2 data types
-----------------
The Tacos2 standard defines storage in:

* Bits
* Registers (16-bit). Can hold integers in the range 0 to 65535 (dec), which is 0 to ffff (hex). Also called 'unsigned INT16' or 'unsigned short'.

Some deviations from the official standard:

**Scaling of register values**
    Some manufacturers store a temperature value of 77.0 C as 770 in the register, to allow room for one decimal.

**Negative numbers (INT16 = short)**
    Some manufacturers allow negative values for some registers. Instead of an allowed integer range 0-65535, a range -32768 to 32767 is allowed. This is implemented as any received value in the upper range (32768-65535) is interpreted as negative value (in the range -32768 to -1). This is two's complement and is described at https://en.wikipedia.org/wiki/Two%27s_complement. Help functions to calculate the two's complement value (and back) are provided in MinimalModbus.
    
**Long integers ('Unsigned INT32' or 'INT32')**
    These require 32 bits, and are implemented as two consecutive 16-bit registers. The range is 0 to 4294967295, which is called 'unsigned INT32'. Alternatively negative values can be stored if the instrument is defined that way, and is then called 'INT32' which has the range -2147483648 to 2147483647.
    
**Floats (single or double precision)**
    Single precision floating point values (binary32) are defined by 32 bits (4 bytes), and are implemented as two consecutive 16-bit registers. Correspondingly, double precision floating point values (binary64) use 64 bits (8 bytes) and are implemented as four consecutive 16-bit registers. How to convert from the bit values to the floating point value is described in the standard IEEE 754, as seen in https://en.wikipedia.org/wiki/Floating_point. Unfortunately the byte order might differ between manufacturers of Modbus instruments.    
    
**Strings**
    Each register (16 bits) is interpreted as two characters (each 1 byte = 8 bits). Often 16 consecutive registers are used, allowing 32 characters in the string. 

**8-bit registers**
    For example Danfoss use 8-bit registers for storage of some settings internally in the instruments. The data is nevertherless transmitted as 16 bit over the serial link, so you can read and write like normal (but with values limited to the range 0-255).
    

Tacos2 implementation details
-----------------------------
In Tacos2 the request message is sent from the master in this format:
    
 * DAS [1 Byte]
 * DAE [1 Byte]
 * CMD [1 Byte]. Allowed value is 0x84 and 0x8F.
 * data [0 to 4 Bytes] 
 * FCC [1 Bytes]. It is a Frame Check Code, for error checking of the message

The response from the client is similar, but with other payload data.

+---------------------------------------+---------------------------------+---------------------------------+
| | CMD                                 | | data to slave                 | | data from slave               | 
| | (in hexadecimal)                    | | (Request)                     | | (Response)                    | 
+=======================================+=================================+=================================+
| | **0x84**                            | | None                          | | None                          | 
| | Stop                                | |                               | |                               | 
+---------------------------------------+---------------------------------+---------------------------------+
| | **0x8E**                            | | None                          | | Height [1~2 Byte]             | 
| | Read heigt and angle                | |                               | | Angle [1~2 Bytes]             | 
+---------------------------------------+---------------------------------+---------------------------------+
| | **0x0F**                            | | Height [0~2 Bytes]            | | height [1~2 Bytes]            | 
| | Set height and angle                | | Angle [0~2 Bytes]             | | Angle [1~2 Bytes]             | 
+---------------------------------------+---------------------------------+---------------------------------+

 TODO Validate


For function code 5, the only valid values are 0000 (hex) or FF00 (hex), representing OFF and ON respectively.

It is seen in the table above that the request and response messages are similar for function code 1 to 4. The same 
can be said about function code 5 and 6, and also about 15 and 16. 

For finding how the k Bytes for the value relates to the number of registers etc (n), see the Modbus documents referred to above.
    

MODBUS ASCII format
-----------------------
This driver also supports Modbus ASCII mode.

Basically, a byte with value 0-255 in Modbus RTU mode will in Modbus ASCII 
mode be sent as two characters corresponding to the hex value of that byte.

For example a value of 76 (dec) = 4C (hex) is sent as the byte 0x4C in Modbus 
RTU mode. This byte happens to correspond to the character 'L' in the ASCII encoding. 
Thus for Modbus RTU this is sent: ``'\x4C'``, which is a string of length 1 and will print as 'L'.

The same value will in Modbus ASCII be sent as the string '4C', which has a length of 2.

The frame format is slightly different for Modbus ASCII. The request message 
is sent from the master in this format:

 * Start [1 character]. It is the colon (:).
 * Slave Address [2 characters]
 * Function code [2 characters]
 * Payload data [0 to 2*252 characters]
 * LRC [2 characters]. The LRC is a Longitudinal Redundancy Check code, for error checking of the message.
 * Stop [2 characters]. 
   The stop characters are carriage return (``'\r'`` = ``'\x0D'``) and line feed (``'\n'`` = ``'\x0A'``).


Manual testing of Modbus equipment
------------------------------------------
Look in your equipment's manual to find working communication examples.

You can make a small Python program to test the communication::

    TODO: Change this to a RTU example

    import serial
    ser = serial.Serial('/dev/ttyUSB0', 19200, timeout=1)
    print ser

    ser.write(':010310010001EA\r\n')
    print repr(ser.read(1000)) # Read 1000 bytes, or wait for timeout

It should print something like::

    Serial<id=0x9faa08c, open=True>(port='/dev/ttyUSB0', baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)
    :0103020136C3

Correspondingly for Modbus ASCII, change the write command to for example::

    TODO: Verify

    ser.write(':010310010001EA\r\n')

It should then print something like::

    Serial<id=0x9faa08c, open=True>(port='/dev/ttyUSB0', baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=False, rtscts=False, dsrdtr=False)
    :0103020136C3

It is also easy to test Modbus ASCII equipment from Linux command line. First must 
the appropriate serial port be set up properly:

 * Print port settings: ``stty -F /dev/ttyUSB0``
 * Print all settings for a port: ``stty -F /dev/ttyUSB0 -a``
 * Reset port to default values: ``stty -F /dev/ttyUSB0 sane``
 * Change port to raw behavior: ``stty -F /dev/ttyUSB0 raw``
 * and: ``stty -F /dev/ttyUSB0 -echo -echoe -echok``
 * Change port baudrate: ``stty -F /dev/ttyUSB0 19200``

To send out a Modbus ASCII request (read register 0x1001 on slave 1), and print out the response::

    cat /dev/ttyUSB0 &
    echo -e ":010310010001EA\r\n" > /dev/ttyUSB0

The reponse will be something like::

    :0103020136C3
    



