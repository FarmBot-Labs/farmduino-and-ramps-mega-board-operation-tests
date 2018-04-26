#!/usr/bin/env python

'''Test FarmBot Arduino/Farmduino electronics with basic firmware commands.'''

from __future__ import print_function
import sys
import time
import serial
import firmware_parameters

HEADER = '''
FarmBot electronics board test commands
for Farmduino or RAMPS/MEGA
v1.7

Press <Enter> at prompts to use (default value)
'''

EXPECTED_FIRMWARE_VERSION = '6.3.0'
RAMPS_PERIPHERAL_PINS = [13, 10, 9, 8]
FARMDUINO_PERIPHERAL_PINS = [13, 7, 8, 9, 10, 12]
SOIL_PIN = 59
EXPECTED_SOIL_SENSOR_VALUE = '>1000'
TOOL_PIN = 63
EXPECTED_TOOL_VERIFICATION_PIN_VALUE = 1

if sys.platform.startswith('linux'):
    DEFAULT_PORT = '/dev/ttyACM0'
elif sys.platform.startswith('darwin'):
    DEFAULT_PORT = '/dev/tty.usbmodem'
else:
    DEFAULT_PORT = 'COM2'

RESPONSE_TIMEOUT = 6  # seconds
PRINT_FIRMWARE_OUTPUT = False  # for debugging
USE_STM32_RESET = False  # as position reset method


def time_elapsed(begin, end):
    '''Calculate time difference in seconds.'''
    return round(end - begin, 2)


def time_test(function):
    '''Time the tests in the category.'''
    def wrapper(*args):
        '''Calculate time elapsed.'''
        start_time = time.time()
        function(*args)
        end_time = time.time()
        return time_elapsed(start_time, end_time)
    return wrapper


def display_warning(text):
    '''Print a warning message.'''
    print('{icon}  {warning}  {icon}'.format(
        icon='*' * 3, warning=text.upper()))


class FarmduinoTestSuite(object):
    '''Test suite.'''

    def __init__(self):
        self.connection = {'serial': None, 'port': None}
        self.options = {'prompts': True, 'verbose': True}
        self.newline = '\n'
        self.test_results = {
            'total':      {'count': 0, 'passed': 0, 'time': 0},
            'misc':       {'count': 0, 'passed': 0, 'time': 0},
            'movement':   {'count': 0, 'passed': 0, 'time': 0},
            'pins':       {'count': 0, 'passed': 0, 'time': 0},
            'parameters': {'count': 0, 'passed': 0, 'time': 0}
            }
        self.board_info = {
            'board': None, 'firmware': None, 'expected_versions': None}
        self.run_mode = None
        self.copy_stdout = None

    def _get_input(self, prompt_text):
        '''Prompt user for input.'''
        input_data = raw_input(prompt_text)
        self.copy_stdout.append_newline()
        return input_data

    def select_port(self):
        '''Select the port of the connected board to test.'''
        self.connection['port'] = (
            self._get_input('serial port ({}): '.format(DEFAULT_PORT))
            or DEFAULT_PORT)
        self.copy_stdout.append_newline()

    def select_board(self):
        '''Choose a board to test.'''
        while True:
            selected_board = (self._get_input(
                'Board to test? 0 for RAMPS, 1 for Farmduino (1): ') or '1')
            if selected_board == '0':
                self.board_info['board'] = 'RAMPS'
                self.board_info['expected_versions'] = [
                    EXPECTED_FIRMWARE_VERSION + '.R']
                break
            elif selected_board == '1':
                self.board_info['board'] = 'Farmduino'
                self.board_info['expected_versions'] = [
                    EXPECTED_FIRMWARE_VERSION + '.F',
                    EXPECTED_FIRMWARE_VERSION + '.G']
                break
        print('{} selected.'.format(self.board_info['board']))

    def connect_to_board(self):
        '''Connect to the board.'''
        while True:
            self.select_port()
            print('Trying to connect to {}...'.format(self.connection['port']))
            try:
                self.connection['serial'] = serial.Serial(
                    self.connection['port'], 115200)
            except serial.serialutil.SerialException:
                print('Serial Error: no connection to {}'.format(
                    self.connection['port']))
            else:
                time.sleep(2)
                print('Connected!', end='\n\n')
                break
        # Check for firmware
        response = ''
        while self.connection['serial'].in_waiting > 0:
            response += self.connection['serial'].read()
        if 'R' not in response:
            print('\nfirmware error: not detected\n'.upper())
            print('Exiting...')
            sys.exit(0)

    def prompt_for_run_mode(self):
        '''Ask user for desired test suite run mode.'''
        print('Test Suite Run Mode Options\n{thin_line}\n'
              '1: Output: full\n'
              '   Prompt: before each test\n'
              #   '2: Output: full only for failed tests\n'
              #   '   Prompt: before each test\n'
              '2: Output: full\n'
              '   Prompt: none\n'
              '3: Output: full only for failed tests\n'
              '   Prompt: none\n'.format(thin_line='-' * 50))
        options = ['1', '2', '3']
        while True:
            response = self._get_input('> ')
            if 'P' in response:
                self._read_position()
            if 'R' in response:
                self._encoder_hard_reset()
            if (any(option in response for option in options)
                    and len(response) == 1):
                if response == '1':
                    self.options['verbose'] = True
                    self.options['prompts'] = True
                # elif response == '2':
                #     self.options['verbose'] = False
                #     self.options['prompts'] = True
                elif response == '2':
                    self.options['verbose'] = True
                    self.options['prompts'] = False
                elif response == '3':
                    self.options['verbose'] = False
                    self.options['prompts'] = False
                self.set_newline()
                self.run_mode = response
                print('Run mode {} selected.'.format(self.run_mode))
                break
            else:
                print('Please input 1, 2, or 3.')

    def set_newline(self):
        '''Set newline characters based on run mode.'''
        if self.options['verbose']:
            self.newline = '\n'
        else:
            self.newline = ''

    def send_command(self, command, expected=None, test_type='misc', quiet=False):
        '''Send a command and print the output.'''
        command_io = {'command': command, 'marker': None, 'expected': expected,
                      'received': None, 'R85': None, 'out': '', 'output': None,
                      'result': 'FAIL'}
        if expected is not None:  # count as a test
            self.update_test_results('count', test_type)
        # Clear input buffer
        self.connection['serial'].reset_input_buffer()
        # Send the command
        if self.options['verbose'] and not quiet:
            print('{:11}{}'.format('SENDING:', command_io['command']))
        self.connection['serial'].write(command + '\r\n')
        # prep for receiving output
        command_io['marker'] = self.get_response_marker(command)
        command_io['out'] = self.get_output()

        if test_type == 'movement':
            # Add check of encoder response
            markers = [command_io['marker'], 'R84']
            indent = ' ' * 2
        else:
            # Prefix of response to check
            markers = [command_io['marker']]
            indent = ''
        for i, marker in enumerate(markers):
            # Separate motor and encoder test results
            if test_type == 'movement':
                if i == 0:
                    print('Motor: ', end=self.newline)
                else:
                    print('Encoder: ', end=self.newline)
                    # Add encoder test to movement test count
                    self.update_test_results('count', test_type)

            if command_io['out'] != '':  # received output
                command_io = self.reduce_output(command_io, marker)

            # Determine test outcome and record as PASS/FAIL
            if command_io['expected'] is not None:
                command_io = self.compare(command_io, test_type)

            # Print sent/received and test results
            self.print_command_io(command_io, indent)

        return command_io['output']

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

    def get_output(self, idle=False, home=False, position=False):
        '''Get command firmware output response.'''
        response = ''
        clock = 0
        delay_increment = 0.005
        while clock < RESPONSE_TIMEOUT:
            time.sleep(delay_increment)
            clock += delay_increment
            while self.connection['serial'].in_waiting > 0:
                response += self.connection['serial'].read()
            if idle:
                if 'R00' in response:
                    # print('idle')
                    break
            elif home:
                if any(zero in response
                       for zero in ['R82 X0 Y0 Z0', 'R82 X0.00 Y0.00 Z0.00']):
                    # print('home')
                    break
            elif position:
                if 'R81' in response:  # R81 is after R85 to get full R85 output
                    # print('encoder position report')
                    break
            else:
                if 'R02' in response or 'R03' in response:
                    # print('got response:')
                    # print(response)
                    break
        else:
            display_warning('response timeout')
        return response

    @staticmethod
    def _find_response(fw_output, marker):
        '''Find the command response in the provided firmware output.'''
        complete_lines = fw_output[:fw_output.rfind('\r\n')]
        ret = complete_lines.split('\r\n')[::-1]  # sort output (last first)
        for line in ret:
            if marker in line:  # response to command sent
                return line
        return

    @staticmethod
    def _reduce_response(response_line):
        '''Return data from the provided command response line (`R# * Q#`).'''
        if response_line is None:
            return
        return (' ').join(response_line.split(' ')[1:-1])

    def reduce_output(self, command_io, marker):
        '''Add the response line and response data to the command_io object.'''
        fw_output = command_io['out']
        command_io['received'] = self._find_response(fw_output, marker)
        command_io['output'] = self._reduce_response(command_io['received'])
        if marker == 'R84':  # include raw and scaled encoder positions
            command_io['R85'] = self._find_response(fw_output, 'R85')
        return command_io

    def compare(self, command_io, test_type):
        '''Compare output to expected value.'''
        expected = command_io['expected']
        output = command_io['output']
        outcome = False
        if command_io['output'] is None:
            outcome = False
        elif any(op in expected for op in ['<', '>', '=']):
            outcome = self._operator_comparison(expected, output)
        elif all(axis in expected for axis in ['X', 'Y', 'Z']):
            outcome = self._delta_comparison(expected, output)
        elif command_io['marker'] == 'R83':  # Firmware version report
            if any(output == v for v in expected):
                outcome = True
        else:
            if output == expected:
                outcome = True

        # Record result of comparison
        if outcome:
            command_io['result'] = 'PASS'
            self.update_test_results('passed', test_type)
        else:
            command_io['result'] = 'FAIL'
        return command_io

    @staticmethod
    def _operator_comparison(expected, output):
        '''Compare using provided operator (for analog pin read).'''
        outcome = False
        pin_compare_value = expected.split('V')[-1]
        pin_output_value = output.split('V')[-1]
        operator = pin_compare_value[0]
        expect = int(pin_compare_value[1:])
        actual = int(pin_output_value)
        if '>' in operator:
            if actual > expect:
                outcome = True
        elif '<' in operator:
            if actual < expect:
                outcome = True
        elif '=' in operator:
            if actual == expect:
                outcome = True
        return outcome

    @staticmethod
    def _delta_comparison(expected, output):
        '''Compare difference in values (for encoder readings).'''
        if output is None:
            display_warning('no output data')
            return False
        move_outcome = True
        move_compare_value = expected.split(' ')
        move_output_value = output.split(' ')
        for i in range(3):
            expect = int(move_compare_value[i][1:])
            actual = int(float(move_output_value[i][1:]))
            difference = abs(actual - expect)
            threshold = 5
            if difference > threshold:
                move_outcome = False
        return move_outcome

    def print_command_io(self, command_io, indent):
        '''Print sent/received for command.'''
        if command_io['result'] == 'FAIL' or self.options['verbose']:
            if command_io['expected'] is not None:
                if (command_io['result'] == 'FAIL'
                        and not self.options['verbose']):
                    print()
                    print('{}{:11}{}'.format(
                        indent, 'SENT:', command_io['command']))
                if PRINT_FIRMWARE_OUTPUT:
                    cleaned_output = command_io['out'].replace('\r*', '*')
                    split_output = cleaned_output.split('\r\n')
                    for i, line in enumerate(split_output):
                        title = 'OUTPUT:' if i == 0 else ''
                        end = '' if i == len(split_output) else '\n'
                        print('{}{:11}{}'.format(indent, title, line), end=end)
                extra_response = ''
                if command_io['R85'] is not None:
                    extra_response += ' ({})'.format(command_io['R85'])
                print('{}{:11}{}{}'.format(
                    indent, 'RECEIVED:', command_io['received'],
                    extra_response))
                print('{}{:11}{}'.format(
                    indent, 'VALUE(S):', command_io['output']))
                print('{}{:11}'.format(
                    indent,
                    '{:11}{}'.format('EXPECTED:', command_io['expected'])))
                print('{}{:11}{}'.format(
                    indent, 'RESULT:', command_io['result']))
                print()
        elif not self.options['verbose']:
            if (command_io['result'] is not None
                    and command_io['received'] is not None):
                print('{}{}'.format(indent, command_io['result']))

    def skip(self, title=None):
        '''Skip test category if requested.'''
        skip_status = False
        if title is not None:
            print('\n{line}\n{title}\n{line}'.format(
                title=title, line='=' * 35))
        if self.options['prompts']:
            if title is not None:
                message = 'Continue?\n'
            else:
                message = 'begin test?'
            skip = self._get_input(message)
            if skip == 's':
                skip_status = True
        return skip_status

    def _restart_connection(self):
        '''Restart arduino connection to clear position.'''
        self.connection['serial'].close()
        self.connection['serial'] = serial.Serial(
            self.connection['port'], 115200)
        time.sleep(2)

    def _encoder_hard_reset(self):
        '''Reset STM32.'''
        # print('resetting STM32...')
        self.send_command('F43 P49 M1', quiet=True)
        self.send_command('F41 P49 V0', quiet=True)
        self.send_command('F41 P49 V1', quiet=True)

    def _read_position(self):
        '''Read and print position.'''
        fw_out = self.get_output(position=True)
        resp = self._find_response(fw_out, 'R85')
        encoder_position = self._reduce_response(resp)
        print('raw encoder positions: {}'.format(encoder_position))

    def _get_board_code(self):
        '''Get single-character board designation.'''
        fw_version = self.board_info['firmware']
        fw_string = '' if fw_version is None else fw_version
        fw_char = [char for char in fw_string][-1]
        return fw_char

    def _reset_position(self):
        '''Reset position to home.'''
        # print('resetting...')
        if USE_STM32_RESET and 'G' in self._get_board_code():
            self._encoder_hard_reset()
        else:
            self.send_command('F84 X1 Y1 Z1', quiet=True)
        self._wait_for_home()

    def _wait_for_idle(self):
        '''Wait for an idle message.'''
        self.get_output(idle=True)

    def _wait_for_home(self):
        '''Wait for a home position report.'''
        self.get_output(home=True)

    @time_test
    def write_parameters(self):
        '''Set firmware parameters to values for testing.'''
        if self.skip('set parameters'.upper()):
            return
        parameters_generator = firmware_parameters.GenerateParameters()
        parameters = parameters_generator.parameters
        for name, axes in parameters.items():
            for axis in axes:
                parameter = axis['num']
                value = axis['value']
                print('{} {}: {} '.format(name, axis['axis'], value),
                      end=self.newline)
                self.send_command('F22 P{} V{}'.format(parameter, value))
                self.send_command('F21 P{}'.format(parameter),
                                  expected='P{} V{}'.format(parameter, value),
                                  test_type='parameters')
        self.send_command('F22 P2 V1')  # Validate parameters
        # self.send_command('F22 P3 V0')  # Don't use EEPROM

    @time_test
    def test_misc(self):
        '''Misc tests.'''
        if self.skip(title='Preliminary tests:'.upper()):
            return
        print('Return firmware version: ', end=self.newline)
        if not self.skip():
            self.board_info['firmware'] = self.send_command(
                'F83', expected=self.board_info['expected_versions'])
            if USE_STM32_RESET and 'G' in self._get_board_code():
                self._encoder_hard_reset()
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
                                  test_type='movement')
                self._reset_position()

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
        if self.board_info['board'] == 'RAMPS':
            pins = RAMPS_PERIPHERAL_PINS
        else:
            pins = FARMDUINO_PERIPHERAL_PINS
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
             'number': SOIL_PIN, 'mode': 1,
             'expected_value': EXPECTED_SOIL_SENSOR_VALUE},
            {'description': 'tool verification (connect to ground)',
             'number': TOOL_PIN, 'mode': 0,
             'expected_value': EXPECTED_TOOL_VERIFICATION_PIN_VALUE}
            ]
        for pin in read_pins:
            mode_text = {'0': 'digital', '1': 'analog'}[str(pin['mode'])]
            print('Read pin {} - {} - {} read mode: '.format(
                pin['number'], pin['description'], mode_text),
                  end=self.newline)
            if not self.skip():
                read_pin(pin['number'], pin['expected_value'], pin['mode'])

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

    def print_results(self):
        '''Print number of passing tests.'''
        print('\n{line}\nTEST RESULTS\n'
              '{board_title:11}{board}\n'
              '{fw_title:11}{fw}\n'
              '{date_title:11}{date} UTC\n'
              '{line}'.format(
                  line='=' * 50,
                  board_title='BOARD:', board=self.board_info['board'],
                  fw_title='FIRMWARE:', fw=self.board_info['firmware'],
                  date_title='TEST DATE:',
                  date=time.strftime('%Y-%m-%d %H:%m', time.gmtime())))
        print('{:12}{:8}{:9}{:10}{:12}'.format(
            'CATEGORY', 'PASS', 'COUNT', 'PERCENT', 'TIME (sec)'))
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

    def run(self):
        '''Run test suite.'''
        # Begin copying stdout for saving to file
        sys.stdout = self.copy_stdout = CarbonCopy()

        # Print header
        print('{line}{header}{line}'.format(line='=' * 50, header=HEADER))

        self.select_board()
        self.connect_to_board()
        self.prompt_for_run_mode()

        suite_start_time = time.time()

        self.test_results['parameters']['time'] = self.write_parameters()
        self.test_results['misc']['time'] = self.test_misc()
        self.test_results['movement']['time'] = self.test_movement()
        self.test_results['pins']['time'] = self.test_pins()

        self.test_results['total']['time'] = time_elapsed(
            suite_start_time, time.time())
        self.print_results()

        self.exit()

        # Save a copy of the output to file
        self.copy_stdout.save_copy_to_file(
            '{}_board-test-results.txt'.format(self.board_info['board']))

    def exit(self):
        '''Close serial and quit.'''
        self.connection['serial'].close()
        notes = self._get_input('Press <Enter> to exit...\n')
        if notes:
            print('Notes: {}'.format(notes))
            print()
        print('Exiting...')


class CarbonCopy(object):
    '''Copy STDOUT to string.'''
    def __init__(self):
        self.stdout = sys.stdout
        self.string = ''

    def write(self, text):
        '''Write to stdout and append a copy to a string.'''
        self.stdout.write(text)
        self.string += text

    def flush(self):
        '''Flush.'''
        pass

    def append_newline(self):
        '''Add an extra newline for use after input prompts.'''
        self.string += '\n'

    def save_copy_to_file(self, filename):
        '''Save the stdout copy to a file.'''
        with open(filename, 'w') as copy_file:
            copy_file.write(self.string)

if __name__ == '__main__':
    FTS = FarmduinoTestSuite()
    FTS.run()
