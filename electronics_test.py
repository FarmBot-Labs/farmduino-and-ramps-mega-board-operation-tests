#!/usr/bin/env python

'''Test basic FarmBot Arduino/Farmduino firmware commands.'''

from __future__ import print_function
import sys
import time
import serial

HEADER = '''
Farmduino test commands
v1.1
Press <Enter> at prompts to use (default value)
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
        self.verbose = True
        if self.verbose:
            self.newline = '\n'
        else:
            self.newline = ''

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

    def skip(self, title=None):
        '''Skip test category if requested.'''
        skip_status = False
        if title is not None:
            print('\n{line}\n{title}\n{line}'.format(
                title=title, line='=' * 35))
        if self.manual:
            if title is not None:
                message = 'Continue?\n'
            else:
                message = 'begin test?'
            skip = raw_input(message)
            if skip == 's':
                skip_status = True
        return skip_status

    @time_test
    def write_parameters(self):
        '''Set firmware parameters to values for testing.'''
        if self.skip('set parameters'.upper()):
            return
        parameters = {
            11: 120, 12: 120, 13: 120,  # movement timeout
            15: 0, 16: 0, 17: 0,  # keep active
            18: 0, 19: 0, 20: 0,  # home at boot
            25: 0, 26: 0, 27: 0,  # enable endstops
            31: 0, 32: 0, 33: 0,  # invert motor
            36: 1, 37: 0,  # second x axis motor
            41: 500, 42: 500, 43: 500,  # acceleration
            45: 0, 46: 0, 47: 0,  # stop at home
            51: 0, 52: 0, 53: 0,  # negatives
            61: 50, 62: 50, 63: 50,  # min speed
            71: 800, 72: 800, 73: 800,  # max speed
            101: 1, 102: 1, 103: 1,  # encoders
            105: 0, 106: 0, 107: 0,  # encoder type
            111: 10, 112: 10, 113: 10,  # missed steps
            115: 100, 116: 100, 117: 100,  # scaling
            121: 10, 122: 10, 123: 10,  # decay
            125: 0, 126: 0, 127: 0,  # positioning
            131: 0, 132: 0, 133: 0,  # invert encoders
            141: 0, 142: 0, 143: 0,  # axis length
            145: 0, 146: 0, 147: 0  # stop at max
            }
        if self.abridged:
            parameters = {'101': 1, '102': 1, '103': 1}  # encoders
        for parameter, value in sorted(parameters.items()):
            print('Set parameter {} to {}: '.format(parameter, value),
                  end=self.newline)
            self.send_command('F22 P{} V{}'.format(parameter, value))
            self.send_command('F21 P{}'.format(parameter),
                              expected='P{} V{}'.format(parameter, value),
                              test_type='parameters')

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
                     delay=0.25):
        '''Send a command and print the output.'''
        command_io = {'command': command, 'marker': None, 'expected': expected,
                      'received': None, 'out': '', 'output': None,
                      'result': 'FAIL'}
        if expected is not None:  # count as a test
            self.update_test_results('count', test_type)
        # Clear input buffer
        self.ser.reset_input_buffer()
        # Send the command
        if self.verbose:
            print('{:11}{}'.format('SENDING:', command_io['command']))
        self.ser.write(command + '\r\n')
        # prep for receiving output
        command_io['marker'] = self.get_response_marker(command)
        time.sleep(delay)
        while self.ser.in_waiting > 0:
            command_io['out'] += self.ser.read()

        if test_type == 'movement':
            markers = [command_io['marker'], 'R84']
            indent = ' ' * 2
        else:
            markers = [command_io['marker']]
            indent = ''
        for i, marker in enumerate(markers):
            if test_type == 'movement':
                if i == 0:
                    print('Motor: ', end=self.newline)
                else:
                    print('Encoder: ', end=self.newline)

            if command_io['out'] != '':  # received output
                command_io = self.reduce_response(command_io, marker)

            if command_io['expected'] is not None:  # record results of test
                if self.compare(command_io['output'], command_io['expected']):
                    command_io['result'] = 'PASS'
                    self.update_test_results('passed', test_type)
                else:
                    command_io['result'] = 'FAIL'

            self.print_command_io(command_io, indent)

        return command_io['output']

    def print_command_io(self, command_io, indent):
        '''Print sent/received for command.'''
        if command_io['result'] == 'FAIL' or self.verbose:
            if command_io['received'] is not None:
                print('{}{:11}{}'.format(
                    indent, 'RECEIVED:', command_io['received']))
            if command_io['output'] is not None:
                print('{}{:11}{}'.format(
                    indent, 'VALUE(S):', command_io['output']))
            if command_io['expected'] is not None:
                print('{}{:11}'.format(
                    indent,
                    '{:11}{}'.format('EXPECTED:', command_io['expected'])))
            if (command_io['result'] is not None
                    and command_io['received'] is not None):
                print('{}{:11}{}'.format(
                    indent, 'RESULT:', command_io['result']))
                print()
        elif not self.verbose:
            if (command_io['result'] is not None
                    and command_io['received'] is not None):
                print('{}{}'.format(indent, command_io['result']))

    @staticmethod
    def reduce_response(command_io, marker):
        '''Get the correct response and return the value.'''
        ret = command_io['out'].split('\r\n')[::-1]  # sort output (last first)
        for line in ret:
            if marker in line:  # response to command sent
                command_io['received'] = line
                # discard marker and `Q`
                command_io['output'] = (' ').join(
                    command_io['received'].split(' ')[1:-1])
                break
        return command_io

    @staticmethod
    def compare(output, expected):
        '''Compare output to expected value.'''
        outcome = False
        compare_value = expected.split('V')[-1]
        if any(op in compare_value for op in ['<', '>', '=']):
            operator = compare_value[0]
            value = int(compare_value[1:])
            if '>' in operator:
                if output > value:
                    outcome = True
            elif '<' in operator:
                if output < value:
                    outcome = True
            elif '=' in operator:
                if output == value:
                    outcome = True
        else:
            if expected in output:
                outcome = True
        return outcome

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
        if self.skip(title='Preliminary tests:'.upper()):
            return
        print('Return firmware version: ', end=self.newline)
        if not self.skip():
            self.firmware = self.send_command(
                'F83', expected='GENESIS.V.01.13.EXPERIMENTAL')

        print('Return current position: ', end=self.newline)
        if not self.skip():
            self.send_command('F82', expected='X0 Y0 Z0')

    @time_test
    def test_movement(self):
        '''Movement tests.'''
        if self.skip(title='Movement tests:'.upper()):
            return
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
                if self.skip():
                    continue
                test_steps = [0, 0, 0]
                test_steps[axis_num] = steps * direction
                self.send_command('G00 X{} Y{} Z{}'.format(*test_steps),
                                  expected='X{} Y{} Z{}'.format(*test_steps),
                                  test_type='movement', delay=5)

    @time_test
    def test_pins(self):
        '''Pin tests.'''
        def read_pin(pin, value, mode):
            '''Send a read pin message.'''
            self.send_command('F42 P{} M{}'.format(pin, mode),
                              expected='P{} V{}'.format(pin, value),
                              test_type='pins')
        if self.skip(title='Pin tests:'.upper()):
            return
        mode = 0
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
                print('Turn pin {} {}: '.format(pin, text_value),
                      end=self.newline)
                if self.skip():
                    continue
                self.send_command('F41 P{} V{} M0'.format(pin, value))
                read_pin(pin, value, mode)
        # Read-only pins
        read_pins = [
            {'description': 'soil sensor',
             'number': 59, 'mode': 1, 'expected_value': '>1000'},
            {'description': 'tool verification (apply 5V)',
             'number': 63, 'mode': 0, 'expected_value': 1}
            ]
        for pin in read_pins:
            mode_text = {'0': 'digital', '1': 'analog'}[str(pin['mode'])]
            print('Read pin {} - {} - {} read mode: '.format(
                pin['number'], pin['description'], mode_text),
                  end=self.newline)
            if not self.skip():
                read_pin(pin['number'], pin['expected_value'], pin['mode'])

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

    def prompt_for_autorun(self):
        '''Ask user to run in automated test suite mode.'''
        response = raw_input('Run tests in manual mode? (True) ').lower()
        options = ['false', 'no', 'n']
        if any(option in response for option in options):
            self.manual = False

    def run(self):
        '''Run test suite.'''
        self.select_board()
        self.connect_to_board()

        self.prompt_for_autorun()

        suite_start_time = time.time()

        self.test_results['parameters']['time'] = self.write_parameters()

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
