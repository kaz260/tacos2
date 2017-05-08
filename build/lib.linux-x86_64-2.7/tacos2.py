#!/usr/bin/env python
#
#   Copyright 2017 Kazuhiro Matsuda
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

"""

.. moduleauthor:: Kazuhiro Matsuda <kazuhiro.matsuda@ane.cmc.osaka-u.ac.jp>

Tacos2: A Python driver for the Tacos2 protocols via serial port (via RS485 or RS232).

"""

__author__   = 'Kazuhiro Matsuda'
__email__    = 'kazuhiro.matsuda@ane.cmc.osaka-u.ac.jp'
__url__      = 'https://github.com/kaz260/tacos2'
__license__  = 'Apache License, Version 2.0'

__version__  = '0.1'
__status__   = 'Beta'


import os
import serial
import struct
import sys
import time

if sys.version > '3':
    import binascii

# Allow long also in Python3
# http://python3porting.com/noconv.html
if sys.version > '3':
    long = int

_NUMBER_OF_BYTES_PER_REGISTER = 2
_SECONDS_TO_MILLISECONDS = 1000

# Several instrument instances can share the same serialport
_SERIALPORTS = {}
_LATEST_READ_TIMES = {}

####################
## Default values ##
####################

BAUDRATE = 9600
"""Default value for the baudrate in Baud (int)."""

PARITY   = serial.PARITY_NONE
"""Default value for the parity. See the pySerial module for documentation. Defaults to serial.PARITY_NONE"""

BYTESIZE = 8
"""Default value for the bytesize (int)."""

STOPBITS = 1
"""Default value for the number of stopbits (int)."""

TIMEOUT  = 0.1
"""Default value for the timeout value in seconds (float)."""

CLOSE_PORT_AFTER_EACH_CALL = False
"""Default value for port closure setting."""

#####################
## Named constants ##
#####################

DLE = 0x10
STX= 0x02
ETX= 0x03
STOP = 0x84
SET = 0x8F
GET = 0x55

##############################
## Tacos2 instrument object ##
##############################


class Instrument():
    """Instrument class for talking to instruments (slaves) via the TacosII protocols (via RS485 or RS232).

    Args:
        * port (str): The serial port name, for example ``/dev/ttyUSB0`` (Linux), ``/dev/tty.usbserial`` (OS X) or ``COM4`` (Windows).
	* devicetype (int): Source device type 
        * sourceaddress (int): Source address

    """

    def __init__(self, port, devicetype=0X00, sourceaddress=0X00):
        if port not in _SERIALPORTS or not _SERIALPORTS[port]:
            self.serial = _SERIALPORTS[port] = serial.Serial(port=port, baudrate=BAUDRATE, parity=PARITY, bytesize=BYTESIZE, stopbits=STOPBITS, timeout=TIMEOUT)
        else:
            self.serial = _SERIALPORTS[port]
            if self.serial.port is None:
                self.serial.open()
        """The serial port object as defined by the pySerial module. Created by the constructor.

        Attributes:
            - port (str):      Serial port name.
                - Most often set by the constructor (see the class documentation).
            - baudrate (int):  Baudrate in Baud.
                - Defaults to :data:`BAUDRATE`.
            - parity (probably int): Parity. See the pySerial module for documentation.
                - Defaults to :data:`PARITY`.
            - bytesize (int):  Bytesize in bits.
                - Defaults to :data:`BYTESIZE`.
            - stopbits (int):  The number of stopbits.
                - Defaults to :data:`STOPBITS`.
            - timeout (float): Timeout value in seconds.
                - Defaults to :data:`TIMEOUT`.
        """

	self.sax = devicetype
	"""Source device type (1Byte) """

        self.sa = sourceaddress
        """source address (1 byte) """

	self.height = 0;
        """ blind hight from floor"""

        self.angle = 0;
        """ slat angle """

        self.slaveAddress = 0x01
        """ client address """

        self.debug = False
        """Set this to :const:`True` to print the communication details. Defaults to :const:`False`."""

        self.close_port_after_each_call = CLOSE_PORT_AFTER_EACH_CALL
        """If this is :const:`True`, the serial port will be closed after each call. Defaults to :data:`CLOSE_PORT_AFTER_EACH_CALL`. To change it, set the value ``tacos2.CLOSE_PORT_AFTER_EACH_CALL=True`` ."""

        self.precalculate_read_size = True
        """If this is :const:`False`, the serial port reads until timeout
        instead of just reading a specific number of bytes. Defaults to :const:`True`.

        New in version 0.5.
        """
        
        self.handle_local_echo = False
        """Set to to :const:`True` if your RS-485 adaptor has local echo enabled. 
        Then the transmitted message will immeadiately appear at the receive line of the RS-485 adaptor.
        Tacos2 will then read and discard this data, before reading the data from the slave.
        Defaults to :const:`False`.

        New in version 0.7.
        """

        if  self.close_port_after_each_call:
            self.serial.close()

    def __repr__(self):
        """String representation of the :class:`.Instrument` object."""
        return "{}.{}<id=0x{:x}, devicetype={}, sourceaddress={}, close_port_after_each_call={}, precalculate_read_size={}, debug={}, serial={}>".format(
            self.__module__,
            self.__class__.__name__,
            id(self),
            self.devicetype,
            self.sourceaddress,
            self.close_port_after_each_call,
            self.precalculate_read_size,
            self.debug,
            self.serial,
            )

    ######################################
    ## Methods for talking to the slave ##
    ######################################
    def stop(self, das, dae):
        """stop Blind control.

        Args:
            * das(destination address start): Start address of the blind to be controlled.
            * dae(destination address end): End address of the blind to be controlled.

        If this command is sended, blind stops operation.
	das must be equal to or less than dae. 

        Returns:
	TODO

        Raises:
            ValueError, TypeError, IOError

        """

        cw = 0xC0
	cmd = STOP
	_checkAddress(das, dae)
        return self._genericCommand(das, dae, cw, cmd)


    def set(self, das, dae, height=255, angle=255):
        """Set Blind heigth from floor and slat angle. Height and angle are represented as percentage.

        Args:
            * das(destination address start): Start address of the blind to be controlled.
            * dae(destination address end): End address of the blind to be controlled.

        Returns:
            Height and angle. 

        Raises:
            ValueError, TypeError, IOError

        """

        cw = 0xC0
	cmd = SET 
        _checkAddress(das, dae)
        return self._genericCommand(das, dae, cw, cmd, height=height, angle=angle)


    def get(self, das):
        """Read blind's height and slat angle.

        Args:
            * das(destination address start): Start address of the blind to be controlled.

        Returns:
            Height and angle

        Raises:
            ValueError, TypeError, IOError

        """

        cw = 0x60
	cmd = GET
	dae = das
        _checkAddress(das, dae)
        return self._genericCommand(das, dae, cw, cmd)

    def setSlaveAddress(self, address):
        """ set slave address """

        if address > 0 or address <= 255:
            self.slaveAddress = address
        else:
            raise ValueError(address)

    def _receive(self):
        """ receive payload from master and respond

        Args:
            None

        Returns:
            Received payload

        Raises:
            ValueError
        """

        payloadFromMaster = []
        pos = 0

        payloadFromMaster += [self.serial.read()]

        while payloadFromMaster[pos] != chr(ETX):
            payloadFromMaster += [self.serial.read()]
            pos += 1

        # read FCC
        payloadFromMaster += [self.serial.read()]

        payloadFromMaster = filter(None, payloadFromMaster)
        print "payload from master:{}".format(repr(payloadFromMaster))

        return payloadFromMaster

    def respond(self):
        """ analyze payload from master
        Args:
            None
        Raises:
            ValueError
        """
        payloadFromMaster = self._receive()

        pos = 2

        if payloadFromMaster[pos] == chr(DLE):
            pos += 1

        bytecount = ord(payloadFromMaster[pos])
        pos += 1

        if payloadFromMaster[pos] == chr(DLE):
            pos += 1

        das = ord(payloadFromMaster[pos])
        pos += 1

        if payloadFromMaster[pos] == chr(DLE):
            pos += 1

        dae = ord(payloadFromMaster[pos])
        pos += 1

        cw = ord(payloadFromMaster[pos])
        pos += 1

        if payloadFromMaster[pos] == chr(DLE):
            pos += 1

        sax = ord(payloadFromMaster[pos])
        pos += 1

        if payloadFromMaster[pos] == chr(DLE):
            pos += 1

        sa = ord(payloadFromMaster[pos])
        pos += 1

        cmd = payloadFromMaster[pos]

        if cmd in (chr(STOP), chr(GET)):
            pos += 3 
            fcc = payloadFromMaster[pos]    

        elif cmd == chr(SET):
            pos += 1
            if payloadFromMaster[pos] == chr(DLE):
                pos += 1

            if ord(payloadFromMaster[pos]) != 255:
                self.height = ord(payloadFromMaster[pos])
            pos += 1

            if payloadFromMaster[pos] == chr(DLE):
                pos += 1

            if ord(payloadFromMaster[pos]) != 255: 
                self.angle = ord(payloadFromMaster[pos])
            pos += 3 

            fcc = payloadFromMaster[pos] 

        if cmd == chr(GET) and (self.slaveAddress == das and self.slaveAddress == dae):
            cw = 0x00
            self._sendResponse(cw)

    def _sendResponse(self, cw):
        if cw == 0x00:
            payloadToMaster = _checkEsc(self.sa) + _checkEsc(self.sa) + _checkEsc(cw)\
                + chr(0x00) + _checkEsc(self.slaveAddress)\
                + chr(GET) + _checkEsc(self.height) + _checkEsc(self.angle)\
                + chr(DLE) + chr(ETX)

        bc = len(payloadToMaster)
        payloadToMaster = chr(bc) + payloadToMaster
        payloadToMaster += chr(_calculateFcc(payloadToMaster))
        payloadToMaster = chr(DLE) + chr(STX) + payloadToMaster

        print "Payload to master:{}".format(repr(payloadToMaster))

        self.serial.write(payloadToMaster)
            
    #####################
    ## Generic command ##
    #####################


    def _genericCommand(self, das, dae, cw, cmd, height=255, angle=255):
        """Generic command for Tacos2.

        Args:
            * das(destination address start): Start address of the blind to be controlled.
            * dae(destination address end): End address of the blind to be controlled.
            * cw: control word
	    * cmd: command

        Returns:
	    * STOP: OK or NG
	    * GET: blind address, height and angle.
	    * SET: OK or NG

        Raises:
            ValueError, TypeError, IOError

        """

        ## Build payload to slave ##
        if cmd in (STOP, GET):
            payloadToSlave = _checkEsc(das) + _checkEsc(dae) + _checkEsc(cw) + \
                             _checkEsc(self.sax) + _checkEsc(self.sa) + \
		 	     chr(cmd) + chr(DLE) + chr(ETX)

        elif cmd == SET:
	    payloadToSlave = _checkEsc(das) + _checkEsc(dae) + _checkEsc(cw) + \
                             _checkEsc(self.sax) + _checkEsc(self.sa) + \
                             chr(cmd) + _checkEsc(height) + _checkEsc(angle) + chr(DLE) + chr(ETX)

	bc = _checkEsc(len(payloadToSlave))

	payloadToSlave = bc + payloadToSlave

	fcc = _calculateFcc(payloadToSlave)

	payloadToSlave = chr(DLE) + chr(STX) + payloadToSlave + chr(fcc)

        ## Communicate ##
        payloadFromSlave = self._performCommand(payloadToSlave, cmd)

        ## Check the contents in the response payload ##
        if cmd == GET:
            return _checkResponse(payloadFromSlave)  # blind address, height and angle 

    ##########################################
    ## Communication implementation details ##
    ##########################################


    def _performCommand(self, payloadToSlave, cmd):
        """Performs the command having the *functioncode*.

        Args:
            * payloadToSlave (str): Data to be transmitted to the slave 

        Returns:
            The extracted data payload from the slave (a string). It has been stripped of FCC etc.

        Raises:
            ValueError, TypeError.

        Makes use of the :meth:`_communicate` method. The request is generated
        with the :func:`_embedPayload` function, and the parsing of the
        response is done with the :func:`_extractPayload` function.

        """

        # Communicate
        response = self._communicate(payloadToSlave, cmd)

        # Extract payload
        if cmd == GET:
            payloadFromSlave = _extractPayload(response)
            return payloadFromSlave


    def _communicate(self, request, cmd):
        """Talk to the slave via a serial port.

        Args:
            request (str): The raw request that is to be sent to the slave.
            cmd (str): Command that is to be sent to the slave.

        Returns:
            The raw data (string) returned from the slave.

        Raises:
            TypeError, ValueError, IOError

        Note that the answer might have strange ASCII control signs, which
        makes it difficult to print it in the promt (messes up a bit).
        Use repr() to make the string printable (shows ASCII values for control signs.)

        If the attribute :attr:`Instrument.debug` is :const:`True`, the communication details are printed.

        If the attribute :attr:`Instrument.close_port_after_each_call` is :const:`True` the
        serial port is closed after each call.

        Timing::

                                                  Request from master (Master is writing)
                                                  |
                                                  |       Response from slave (Master is reading)
                                                  |       |
            ----W----R----------------------------W-------R----------------------------------------
                     |                            |       |
                     |<----- Silent period ------>|       |
                                                  |       |
                             Roundtrip time  ---->|-------|<--

        The resolution for Python's time.time() is lower on Windows than on Linux.
        It is about 16 ms on Windows according to
        http://stackoverflow.com/questions/157359/accurate-timestamping-in-python

        For Python3, the information sent to and from pySerial should be of the type bytes.
        This is taken care of automatically by Tacos2.
        
        

        """

        if self.debug:
            _print_out('\nTacos2 debug mode. Writing to instrument : {!r} ({})'. \
                format(request, _hexlify(request)))

        if self.close_port_after_each_call:
            self.serial.open()

        #self.serial.flushInput() TODO

        if sys.version_info[0] > 2:
            request = bytes(request, encoding='latin1')  # Convert types to make it Python3 compatible

        # Sleep to make sure 3.5 character times have passed
        minimum_silent_period   = _calculate_minimum_silent_period(self.serial.baudrate)
        time_since_read         = time.time() - _LATEST_READ_TIMES.get(self.serial.port, 0)

        if time_since_read < minimum_silent_period:
            sleep_time = minimum_silent_period - time_since_read

            if self.debug:
                template = 'Tacos2 debug mode. Sleeping for {:.1f} ms. ' + \
                        'Minimum silent period: {:.1f} ms, time since read: {:.1f} ms.'
                text = template.format(
                    sleep_time * _SECONDS_TO_MILLISECONDS,
                    minimum_silent_period * _SECONDS_TO_MILLISECONDS,
                    time_since_read * _SECONDS_TO_MILLISECONDS)
                _print_out(text)

            time.sleep(sleep_time)

        elif self.debug:
            template = 'Tacos2 debug mode. No sleep required before write. ' + \
                'Time since previous read: {:.1f} ms, minimum silent period: {:.2f} ms.'
            text = template.format(
                time_since_read * _SECONDS_TO_MILLISECONDS,
                minimum_silent_period * _SECONDS_TO_MILLISECONDS)
            _print_out(text)

        # Write request
        latest_write_time = time.time()
        
        self.serial.write(request)

        # Read and discard local echo
        if self.handle_local_echo:
            localEchoToDiscard = self.serial.read(len(request))
            if self.debug:
                template = 'Tacos2 debug mode. Discarding this local echo: {!r} ({} bytes).' 
                text = template.format(localEchoToDiscard, len(localEchoToDiscard))
                _print_out(text)
            if localEchoToDiscard != request:
                template = 'Local echo handling is enabled, but the local echo does not match the sent request. ' + \
                    'Request: {!r} ({} bytes), local echo: {!r} ({} bytes).' 
                text = template.format(request, len(request), localEchoToDiscard, len(localEchoToDiscard))
                raise IOError(text)

        # Read response
        # When only "GET" command is sent to the slave, the slave will return a response.
        NUMBER_OF_BYTES_TO_READ = 20

        if cmd == GET:
            answer = self.serial.read(NUMBER_OF_BYTES_TO_READ)
            _LATEST_READ_TIMES[self.serial.port] = time.time()

            if self.close_port_after_each_call:
                self.serial.close()

            if sys.version_info[0] > 2:
                answer = str(answer, encoding='latin1')  # Convert types to make it Python3 compatible

            if self.debug:
                template = 'Tacos2 debug mode. Response from instrument: {!r} ({}) ({} bytes), ' + \
                    'roundtrip time: {:.1f} ms. Timeout setting: {:.1f} ms.\n'
                text = template.format(
                    answer,
                    _hexlify(answer),
                    len(answer),
                    (_LATEST_READ_TIMES.get(self.serial.port, 0) - latest_write_time) * _SECONDS_TO_MILLISECONDS,
                    self.serial.timeout * _SECONDS_TO_MILLISECONDS)
                _print_out(text)

            if len(answer) == 0:
                raise IOError('No communication with the instrument (no answer)')

            return answer

####################
# Payload handling #
####################


def _extractPayload(response):
    """Extract the payload data part from the slave's response.

    Args:
        * response (str): The raw response byte string from the slave.

    Returns:
        The payload part of the *response* string.

    Raises:
        ValueError, TypeError. Raises an exception if there is any problem with the received address, the functioncode or the CRC.

    For development purposes, this function can also be used to extract the payload from the request sent TO the slave.

    """
    # extract bytecount and check it
    print "response:{}".format(repr(response))
    pos = 2
    bytecount = ord(response[pos])
    pos += 1

    if bytecount < 6:
        raise ValueError(bytecount)

    subframe = response[2:3+bytecount]

    # extract DA
    if ord(subframe[pos]) == DLE:
        pos += 1
    da = ord(subframe[pos])
    pos += 1

    # extract CW
    if ord(subframe[pos]) == DLE:
        pos += 1
    cw = ord(subframe[pos])
    pos += 1

    # extract SAX
    if ord(subframe[pos]) == DLE:
        pos += 1
    sax = ord(subframe[pos])
    pos += 1

    # extract SA
    if ord(subframe[pos]) == DLE:
        pos += 1
    sa = ord(subframe[pos])
    pos += 1

    # extract cmd
    cmd = ord(subframe[pos]) 

    return subframe


############################################
## Serial communication utility functions ##
############################################


def _calculate_minimum_silent_period(baudrate):
    """Calculate the silent period length to comply with the 3.5 character silence between messages.

    Args:
        baudrate (numerical): The baudrate for the serial port

    Returns:
        The number of seconds (float) that should pass between each message on the bus.

    Raises:
        ValueError, TypeError.

    """
    _checkNumerical(baudrate, minvalue=1, description='baudrate')  # Avoid division by zero

    BITTIMES_PER_CHARACTERTIME = 11
    MINIMUM_SILENT_CHARACTERTIMES = 3.5

    bittime = 1 / float(baudrate)
    return bittime * BITTIMES_PER_CHARACTERTIME * MINIMUM_SILENT_CHARACTERTIMES

##############################
# String and num conversions #
##############################

def _hexencode(bytestring, insert_spaces = False):
    """Convert a byte string to a hex encoded string.

    For example 'J' will return '4A', and ``'\\x04'`` will return '04'.

    Args:
        bytestring (str): Can be for example ``'A\\x01B\\x45'``.
        insert_spaces (bool): Insert space characters between pair of characters to increase readability.

    Returns:
        A string of twice the length, with characters in the range '0' to '9' and 'A' to 'F'.
        The string will be longer if spaces are inserted.

    Raises:
        TypeError, ValueError

    """
    _checkString(bytestring, description='byte string')

    separator = '' if not insert_spaces else ' '
    
    # Use plain string formatting instead of binhex.hexlify,
    # in order to have it Python 2.x and 3.x compatible

    byte_representions = []
    for c in bytestring:
        byte_representions.append( '{0:02X}'.format(ord(c)) )
    return separator.join(byte_representions).strip()


def _hexdecode(hexstring):
    """Convert a hex encoded string to a byte string.

    For example '4A' will return 'J', and '04' will return ``'\\x04'`` (which has length 1).

    Args:
        hexstring (str): Can be for example 'A3' or 'A3B4'. Must be of even length.
        Allowed characters are '0' to '9', 'a' to 'f' and 'A' to 'F' (not space).

    Returns:
        A string of half the length, with characters corresponding to all 0-255 values for each byte.

    Raises:
        TypeError, ValueError

    """
    # Note: For Python3 the appropriate would be: raise TypeError(new_error_message) from err
    # but the Python2 interpreter will indicate SyntaxError.
    # Thus we need to live with this warning in Python3:
    # 'During handling of the above exception, another exception occurred'

    _checkString(hexstring, description='hexstring')

    if len(hexstring) % 2 != 0:
        raise ValueError('The input hexstring must be of even length. Given: {!r}'.format(hexstring))

    if sys.version_info[0] > 2:
        by = bytes(hexstring, 'latin1')
        try:
            return str(binascii.unhexlify(by), encoding='latin1')
        except binascii.Error as err:
            new_error_message = 'Hexdecode reported an error: {!s}. Input hexstring: {}'.format(err.args[0], hexstring)
            raise TypeError(new_error_message)

    else:
        try:
            return hexstring.decode('hex')
        except TypeError as err:
            raise TypeError('Hexdecode reported an error: {}. Input hexstring: {}'.format(err.message, hexstring))


def _hexlify(bytestring):
    """Convert a byte string to a hex encoded string, with spaces for easier reading.
    
    This is just a facade for _hexencode() with insert_spaces = True.
    
    See _hexencode() for details.

    """
    return _hexencode(bytestring, insert_spaces = True)


def _bitResponseToValue(bytestring):
    """Convert a response string to a numerical value.

    Args:
        bytestring (str): A string of length 1. Can be for example ``\\x01``.

    Returns:
        The converted value (int).

    Raises:
        TypeError, ValueError

    """
    _checkString(bytestring, description='bytestring', minlength=1, maxlength=1)

    RESPONSE_ON  = '\x01'
    RESPONSE_OFF = '\x00'

    if bytestring == RESPONSE_ON:
        return 1
    elif bytestring == RESPONSE_OFF:
        return 0
    else:
        raise ValueError('Could not convert bit response to a value. Input: {0!r}'.format(bytestring))


############################
# Error checking functions #
############################

def _checkNumerical(inputvalue, minvalue=None, maxvalue=None, description='inputvalue'):
    """Check that the given numerical value is valid.

    Args:
        * inputvalue (numerical): The value to be checked.
        * minvalue (numerical): Minimum value  Use None to skip this part of the test.
        * maxvalue (numerical): Maximum value. Use None to skip this part of the test.
        * description (string): Used in error messages for the checked inputvalue

    Raises:
        TypeError, ValueError

    Note: Can not use the function :func:`_checkString`, as it uses this function internally.

    """
    # Type checking
    if not isinstance(description, str):
        raise TypeError('The description should be a string. Given: {0!r}'.format(description))

    if not isinstance(inputvalue, (int, long, float)):
        raise TypeError('The {0} must be numerical. Given: {1!r}'.format(description, inputvalue))

    if not isinstance(minvalue, (int, float, long, type(None))):
        raise TypeError('The minvalue must be numeric or None. Given: {0!r}'.format(minvalue))

    if not isinstance(maxvalue, (int, float, long, type(None))):
        raise TypeError('The maxvalue must be numeric or None. Given: {0!r}'.format(maxvalue))

    # Consistency checking
    if (not minvalue is None) and (not maxvalue is None):
        if maxvalue < minvalue:
            raise ValueError('The maxvalue must not be smaller than minvalue. Given: {0} and {1}, respectively.'.format( \
                maxvalue, minvalue))

    # Value checking
    if not minvalue is None:
        if inputvalue < minvalue:
            raise ValueError('The {0} is too small: {1}, but minimum value is {2}.'.format( \
                description, inputvalue, minvalue))

    if not maxvalue is None:
        if inputvalue > maxvalue:
            raise ValueError('The {0} is too large: {1}, but maximum value is {2}.'.format( \
                description, inputvalue, maxvalue))


def _checkString(inputstring, description, minlength=0, maxlength=None):
    """Check that the given string is valid.

    Args:
        * inputstring (string): The string to be checked
        * description (string): Used in error messages for the checked inputstring
        * minlength (int): Minimum length of the string
        * maxlength (int or None): Maximum length of the string

    Raises:
        TypeError, ValueError

    Uses the function :func:`_checkInt` internally.

    """
    # Type checking
    if not isinstance(description, str):
        raise TypeError('The description should be a string. Given: {0!r}'.format(description))

    if not isinstance(inputstring, str):
        raise TypeError('The {0} should be a string. Given: {1!r}'.format(description, inputstring))

    if not isinstance(maxlength, (int, type(None))):
        raise TypeError('The maxlength must be an integer or None. Given: {0!r}'.format(maxlength))

    # Check values
    _checkInt(minlength, minvalue=0, maxvalue=None, description='minlength')

    if len(inputstring) < minlength:
        raise ValueError('The {0} is too short: {1}, but minimum value is {2}. Given: {3!r}'.format( \
            description, len(inputstring), minlength, inputstring))

    if not maxlength is None:
        if maxlength < 0:
            raise ValueError('The maxlength must be positive. Given: {0}'.format(maxlength))

        if maxlength < minlength:
            raise ValueError('The maxlength must not be smaller than minlength. Given: {0} and {1}'.format( \
                maxlength, minlength))

        if len(inputstring) > maxlength:
            raise ValueError('The {0} is too long: {1}, but maximum value is {2}. Given: {3!r}'.format( \
                description, len(inputstring), maxlength, inputstring))

def _checkInt(inputvalue, minvalue=None, maxvalue=None, description='inputvalue'):
    """Check that the given integer is valid.

    Args:
        * inputvalue (int or long): The integer to be checked
        * minvalue (int or long, or None): Minimum value of the integer
        * maxvalue (int or long, or None): Maximum value of the integer
        * description (string): Used in error messages for the checked inputvalue

    Raises:
        TypeError, ValueError

    Note: Can not use the function :func:`_checkString`, as that function uses this function internally.

    """
    if not isinstance(description, str):
        raise TypeError('The description should be a string. Given: {0!r}'.format(description))

    if not isinstance(inputvalue, (int, long)):
        raise TypeError('The {0} must be an integer. Given: {1!r}'.format(description, inputvalue))

    if not isinstance(minvalue, (int, long, type(None))):
        raise TypeError('The minvalue must be an integer or None. Given: {0!r}'.format(minvalue))

    if not isinstance(maxvalue, (int, long, type(None))):
        raise TypeError('The maxvalue must be an integer or None. Given: {0!r}'.format(maxvalue))

    _checkNumerical(inputvalue, minvalue, maxvalue, description)


#####################
# Development tools #
#####################


def _print_out(inputstring):
    """Print the inputstring. To make it compatible with Python2 and Python3.

    Args:
        inputstring (str): The string that should be printed.

    Raises:
        TypeError

    """
    _checkString(inputstring, description='string to print')

    sys.stdout.write(inputstring + '\n')


def _getDiagnosticString():
    """Generate a diagnostic string, showing the module version, the platform, current directory etc.

    Returns:
        A descriptive string.

    """
    text = '\n## Diagnostic output from tacos2 ## \n\n'
    text += 'Tacos2 version: ' + __version__ + '\n'
    text += 'Tacos2 status: ' + __status__ + '\n'
    text += 'File name (with relative path): ' + __file__ + '\n'
    text += 'Full file path: ' + os.path.abspath(__file__) + '\n\n'
    text += 'pySerial version: ' + serial.VERSION + '\n'
    text += 'pySerial full file path: ' + os.path.abspath(serial.__file__) + '\n\n'
    text += 'Platform: ' + sys.platform + '\n'
    text += 'Filesystem encoding: ' + repr(sys.getfilesystemencoding()) + '\n'
    text += 'Byteorder: ' + sys.byteorder + '\n'
    text += 'Python version: ' + sys.version + '\n'
    text += 'Python version info: ' + repr(sys.version_info) + '\n'
    text += 'Python flags: ' + repr(sys.flags) + '\n'
    text += 'Python argv: ' + repr(sys.argv) + '\n'
    text += 'Python prefix: ' + repr(sys.prefix) + '\n'
    text += 'Python exec prefix: ' + repr(sys.exec_prefix) + '\n'
    text += 'Python executable: ' + repr(sys.executable) + '\n'
    try:
        text += 'Long info: ' + repr(sys.long_info) + '\n'
    except:
        text += 'Long info: (none)\n'  # For Python3 compatibility
    try:
        text += 'Float repr style: ' + repr(sys.float_repr_style) + '\n\n'
    except:
        text += 'Float repr style: (none) \n\n'  # For Python 2.6 compatibility
    text += 'Variable __name__: ' + __name__ + '\n'
    text += 'Current directory: ' + os.getcwd() + '\n\n'
    text += 'Python path: \n'
    text += '\n'.join(sys.path) + '\n'
    text += '\n## End of diagnostic output ## \n'
    return text


def _checkAddress(das, dae):
    """ Check das is equal to or less than dae.

    Args:
        * das (destination address start)
        * dae (destination address end)
    Raises:
	ValueError

    """
    if not(das <= dae):
        raise ValueError('The DAS{0} must be equal to or less than DAE{0}'.format(das, dae))


def _checkEsc(data):
    """ Check whether escape code is necessary """
    if data == 0x10:
        return chr(DLE) + chr(data)
    else:
        return chr(data)


def _calculateFcc(payload):
    """ Calculate frame check code.
	add all bytes and calculete two's complement
    """

    sum = 0

    for i in range(len(payload)):
        sum += ord(payload[i])

    return (~sum + 1) & 0xFF


def _checkResponse(response):
    """ check response 
    """
    print "response:{}".format(repr(response))
    pos = 0 

    if response[pos] == chr(DLE):
        pos += 1

    bytecount = response[pos]
    pos += 1

    if response[pos] == chr(DLE):
        pos += 1

    das = response[pos]
    pos += 1

    if response[pos] == chr(DLE):
        pos += 1

    dae = response[pos]
    pos += 1

    cw = response[pos]
    pos += 1

    if response[pos] == chr(DLE):
        pos += 1

    sax = response[pos]
    pos += 1

    if response[pos] == chr(DLE):
        pos += 1

    sa = response[pos]
    pos += 1

    res = response[pos]
    pos += 1

    if res == chr(GET):
        if response[pos] == chr(DLE):
            pos += 1

        if ord(response[pos]) != 255:
            height = response[pos]
            print "height:{}".format(ord(height))
        pos += 1

        if response[pos] == chr(DLE):
            pos += 1

        if ord(response[pos]) != 255:
            angle = response[pos]
            print "angle:{}".format(ord(angle))
        pos += 2 

        fcc = response[pos]

    return height, angle 
