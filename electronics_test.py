#!/usr/bin/env python

'''Test basic FarmBot Arduino/Farmduino firmware commands.'''

from __future__ import print_function
import sys
import time
import serial

HEADER = '''
Farmduino test commands
v1.0
'''

if sys.platform.startswith('linux'):
    DEFAULT_PORT = '/dev/ttyACM0'
elif sys.platform.startswith('darwin'):
    DEFAULT_PORT = '/dev/tty.usbmodem'
else:
    DEFAULT_PORT = 'COM2'


def time_test(function):
    '''Time the tests in the category.'''
    def wrapper(*args):
        '''Calculate time elapsed.'''
        start_time = time.time()
        function(*args)
        end_time = time.time()
        elapsed_minutes = round(int(end_time - start_time) / 60., 1)
        return elapsed_minutes
    return wrapper


class FarmduinoTestSuite(object):
    '''Test suite.'''

    def __init__(self):
        print('{line}{header}{line}'.format(line='=' * 50, header=HEADER))
        self.port = (
            raw_input('serial port ({}): '.format(DEFAULT_PORT))
            or DEFAULT_PORT
            )
        self.ser = None
        self.manual = True
        self.test_results = {
            'total': {'count': 0, 'passed': 0, 'time': 0},
            'misc': {'count': 0, 'passed': 0, 'time': 0},
            'movement': {'count': 0, 'passed': 0, 'time': 0},
            'pins': {'count': 0, 'passed': 0, 'time': 0},
            'parameters': {'count': 0, 'passed': 0, 'time': 0}
            }
        self.abridged = False
        self.board = None
        self.firmware = None

    def connect_to_board(self):
        '''Connect to the board.'''
        print('Trying to connect to {}...'.format(self.port))
        try:
            self.ser = serial.Serial(self.port, 115200)
        except serial.serialutil.SerialException:
            print('Serial Error: no connection to {}'.format(self.port))
            print('Exiting...')
            sys.exit()
        else:
            time.sleep(2)
            print('Connected!', end='\n\n')

    @time_test
    def write_parameters(self):
        '''Set firmware parameters to values for testing.'''
        print('{line}\nSET PARAMETERS\n{line}'.format(line='=' * 35))
        parameters = {
            '11': 120, '12': 120, '13': 120,  # movement timeout
            '15': 0, '16': 0, '17': 0,  # keep active
            '18': 0, '19': 0, '20': 0,  # home at boot
            '25': 0, '26': 0, '27': 0,  # enable endstops
            '31': 0, '32': 0, '33': 0,  # invert motor
            '36': 1, '37': 0,  # second x axis motor
            '41': 500, '42': 500, '43': 500,  # acceleration
            '45': 0, '46': 0, '47': 0,  # stop at home
            '51': 0, '52': 0, '53': 0,  # negatives
            '61': 50, '62': 50, '63': 50,  # min speed
            '71': 800, '72': 800, '73': 800,  # max speed
            '101': 1, '102': 1, '103': 1,  # encoders
            '105': 0, '106': 0, '107': 0,  # encoder type
            '111': 10, '112': 10, '113': 10,  # missed steps
            '115': 100, '116': 100, '117': 100,  # scaling
            '121': 10, '122': 10, '123': 10,  # decay
            '125': 0, '126': 0, '127': 0,  # positioning
            '131': 0, '132': 0, '133': 0,  # invert encoders
            '141': 0, '142': 0, '143': 0,  # axis length
            '145': 0, '146': 0, '147': 0  # stop at max
            }
        if self.abridged:
            parameters = {'101': 1, '102': 1, '103': 1}  # encoders
        for parameter, value in parameters.items():
            self.send_command('F22 P{} V{}'.format(parameter, value),
                              skip_wait=True)
            self.send_command('F21 P{}'.format(parameter),
                              expected='P{} V{}'.format(parameter, value),
                              test_type='parameters',
                              skip_wait=True)

    def update_test_results(self, result_category, test_category):
        '''Update the test results summary.'''
        self.test_results['total'][result_category] += 1
        if 'movement' in test_category:
            self.test_results['movement'][result_category] += 1
        elif 'pins' in test_category:
            self.test_results['pins'][result_category] += 1
        elif 'parameters' in test_category:
            self.test_results['parameters'][result_category] += 1
        else:
            self.test_results['misc'][result_category] += 1

    @staticmethod
    def get_response_marker(command):
        '''Determine the marker that will indicate the response.'''
        if 'G0' in command:  # movement
            marker = 'R82'
        elif 'F42' in command:  # pin
            marker = 'R41'
        else:
            marker = 'R' + command[1:3]
        return marker

    def send_command(self, command, expected=None, test_type='misc',
                     skip_wait=False, delay=0.25):
        '''Send a command and print the output.'''
        if expected is not None:  # count as a test
            self.update_test_results('count', test_type)
        # Clear input buffer
        self.ser.reset_input_buffer()
        # Send the command
        print('{:11}{}'.format('SENDING:', command))
        self.ser.write(command + '\r\n')
        # prep for receiving output
        marker = self.get_response_marker(command)
        out = ''
        output = None
        time.sleep(delay)
        while self.ser.in_waiting > 0:
            out += self.ser.read()

        if test_type == 'movement':
            markers = [marker, 'R84']
        else:
            markers = [marker]
        for marker in markers:
            if out != '':  # received output
                print('{:11}'.format('RECEIVED:'), end='')
                ret = out.split('\r\n')[::-1]  # sort output (latest first)
                for line in ret:
                    if marker in line:  # response to command sent
                        print(line)
                        # discard marker and `Q`
                        output = (' ').join(line.split(' ')[1:-1])
                        print('{:11}'.format('VALUE(S):'), end='')
                        print(output)  # value in response
                        break

            if expected is not None:  # record results of test
                print('{:11}'.format('{:11}{}'.format('EXPECTED:', expected)))
                if expected in output:  # sucess
                    result = 'PASS'
                    self.update_test_results('passed', test_type)
                else:
                    result = 'FAIL'
                print('{:11}{}'.format('RESULT:', result))

        print()

        if self.manual and not skip_wait:
            self.next()  # prompt user to continue to the next test

        return output

    @staticmethod
    def begin():
        '''Wait for user to press <Enter>.'''
        raw_input('Press <Enter> to begin the tests...\n')

    @staticmethod
    def next():
        '''Wait for user to press <Enter>.'''
        raw_input('Press <Enter> to continue to the next test...\n')

    def print_results(self):
        '''Print number of passing tests.'''
        print('{line}\nTEST RESULTS\n'
              '{board_title:11}{board}\n{fw_title:11}{fw}\n{line}'.format(
                  line='=' * 50, board_title='BOARD:', board=self.board,
                  fw_title='FIRMWARE:', fw=self.firmware))
        print('{:12}{:8}{:9}{:10}{:12}'.format(
            'CATEGORY', 'PASS', 'COUNT', 'PERCENT', 'TIME (min)'))
        for cat in ['total', 'misc', 'movement', 'pins', 'parameters']:
            passed = self.test_results[cat]['passed']
            count = self.test_results[cat]['count']
            elapsed = self.test_results[cat]['time']
            if count > 0:
                percent = int(round(float(passed) / count * 100, 0))
            else:
                percent = 0
            print('{:12}{:3}{:8}{:10}%{:12}'.format(
                cat, passed, count, percent, elapsed))
        print('{line}\n'.format(line='=' * 50))

    @time_test
    def test_misc(self):
        '''Misc tests.'''
        print('Return firmware version:')
        self.firmware = self.send_command(
            'F83', expected='GENESIS.V.01.13.EXPERIMENTAL')

        print('Return current position:')
        self.send_command('F82', expected='X0 Y0 Z0')

    @time_test
    def test_movement(self):
        '''Movement tests.'''
        steps = 200
        axes = ['X', 'Y', 'Z']
        if self.abridged:
            axes = ['X']
        for axis_num, axis in enumerate(axes):
            for direction in [1, -1]:
                if direction > 0:
                    text_direction = 'forward'
                else:
                    text_direction = 'backward'
                print('Move {} axis {}:'.format(axis, text_direction))
                test_steps = [0, 0, 0]
                test_steps[axis_num] = steps * direction
                self.send_command('G00 X{} Y{} Z{}'.format(*test_steps),
                                  expected='X{} Y{} Z{}'.format(*test_steps),
                                  test_type='movement', delay=5)

    @time_test
    def test_pins(self):
        '''Pin tests.'''
        if self.board == 'RAMPS':
            pins = [13, 10, 9, 8]
            if self.abridged:
                pins = [13]
        else:
            pins = [7, 8, 9, 10, 12]
        for pin in pins:
            for value in [1, 0]:
                if value > 0:
                    text_value = 'on'
                else:
                    text_value = 'off'
                print('Turn pin {} {}:'.format(pin, text_value))
                self.send_command(
                    'F41 P{} V{} M0'.format(pin, value), skip_wait=True)
                self.send_command('F42 P{} M0'.format(pin),
                                  expected='P{} V{}'.format(pin, value),
                                  test_type='pins')
        # Tool verification pin (expecting 5V)
        pin = 9
        value = 1
        print('Read pin {}:'.format(pin))
        self.send_command('F42 P{} M0'.format(pin),
                          expected='P{} V{}'.format(pin, value),
                          test_type='pins')
        # Soil Sensor pin
        pin = 5
        value = 0
        print('Read pin {}:'.format(pin))
        self.send_command('F42 P{} M1'.format(pin),
                          expected='P{} V{}'.format(pin, value),
                          test_type='pins')

    def select_board(self):
        '''Choose a board to test.'''
        selected_board = (
            raw_input('Board to test? 0 for RAMPS, 1 for Farmduino (1) ')
            or 1)
        if int(selected_board) > 0:
            self.board = 'Farmduino'
        else:
            self.board = 'RAMPS'
        print('{} selected.'.format(self.board))

    def run(self):
        '''Run test suite.'''
        self.select_board()
        self.connect_to_board()

        self.manual = (
            raw_input('Run tests in manual mode? (True) ')
            or True)

        suite_start_time = time.time()

        self.test_results['parameters']['time'] = self.write_parameters()

        if self.manual:
            self.begin()  # prompt user to begin

        self.test_results['misc']['time'] = self.test_misc()
        self.test_results['movement']['time'] = self.test_movement()
        self.test_results['pins']['time'] = self.test_pins()

        self.test_results['total']['time'] = round(
            int(time.time() - suite_start_time) / 60., 1)

        self.print_results()

        self.exit()

    def exit(self):
        '''Close serial and quit.'''
        self.ser.close()
        raw_input('Press <Enter> to exit...\n')
        print('Exiting...')

if __name__ == '__main__':
    FTS = FarmduinoTestSuite()
    FTS.run()
