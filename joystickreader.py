# (c) Anton Osten for the PyBot Project

# in case we're run from python2
from __future__ import division
import serial


# for when the joystick is not at the specified port
class BadPortError(serial.serialutil.SerialException):
    def __init__(self, message):
        self.message = message
    
    def __str__(self):
        return self.message

# a custom exception for when we are given bad data
class BadInputError(Exception):
    def __init__(self, message='Bad input data'):
        self.message = message
    
    def __str__(self):
        return self.message

class JoystickReader(object):
    def __init__(self, port='/dev/tty.usbmodemfd121', baudrate=9600, x_zero=133, y_zero=127):
        try:
            self.ser = serial.Serial(port, baudrate=baudrate)
        except serial.serialutil.SerialException:
            raise BadPortError("Couldn't connect on {}. Try a different port.".format(port))
        self._x_zero = x_zero
        self._y_zero = y_zero
        
    def read_values(self):
        line = self.ser.readline().decode('ascii')
        values = line.strip().split(' ')
        if values[0] != '0' or len(values) is not 4:
            raise BadInputError
        del values[0]
        values = [int(value) for value in values]
        assert len(values) is 3, 'there should be 3 output values'
        return values
    
    def calibrate(self, y_zero=None, x_zero=None):
        if y_zero is not None:
            self._y_zero = y_zero
        if x_zero is not None:
            self._x_zero = x_zero

    def interpret_values(self, sorted_values=None):
        '''Interprets the pre-sorted joystick data.
        Raises BadInputError when there is something wrong with the data.'''
        if sorted_values is None:
            sorted_values = self.read_values()
        button_value = sorted_values[0]
        # let's check that we are given correctly sorted values with the right data 
        # (3 items, button value, which is at index 0, has to be 1 or 2)
        if len(sorted_values) > 3 or button_value not in {1, 2}:
            raise BadInputError
        # okay, if the data are right, then let's interpret them
        # the button is pressed when its value is 1 (and not pressed when it's 2)
        button_pressed = True if button_value is 1 else False
        # now let's work on x and y
        y = sorted_values[1] - self._y_zero
        x = sorted_values[2] - self._x_zero
        # the range for x and y is 1-250
        # from experience we know that zero for y is at 126
        # (we need to account for them sometimes being at 1 even when they aren't pressed)
        if y > 1:
            y_direction = 'up'
        elif y < -1:
            y_direction = 'down'
        else:
            y_direction = None
        # and zero for x is between 132 and 134
        if x > 1:
            x_direction = 'left'
        elif x < -1:
            x_direction = 'right'
        else:
            x_direction = None
        # now let's split each direction into 'steps'
        # i.e. how far is the joystick moved in a particular direction
        y_steps = round(abs(y) / 10)
        x_steps = round(abs(x) / 10)
    
        return {'button_pressed': button_pressed,
        'y_value': y, 'y_direction': y_direction, 'y_steps': y_steps,
        'x_value': x, 'x_direction': x_direction, 'x_steps': x_steps}