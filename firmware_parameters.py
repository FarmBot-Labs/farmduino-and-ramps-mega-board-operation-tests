#!/usr/bin/env python

'''Parameters Table Generation.'''

from __future__ import print_function
from collections import OrderedDict

PARAMETERS = {
    'Movement timeout (seconds)': [
        {'axis': 'x', 'num': 11, 'value': 120},
        {'axis': 'y', 'num': 12, 'value': 120},
        {'axis': 'z', 'num': 13, 'value': 120}],
    'Keep motor active': [
        {'axis': 'x', 'num': 15, 'value': 0},
        {'axis': 'y', 'num': 16, 'value': 0},
        {'axis': 'z', 'num': 17, 'value': 0}],
    'Home at boot': [
        {'axis': 'x', 'num': 18, 'value': 0},
        {'axis': 'y', 'num': 19, 'value': 0},
        {'axis': 'z', 'num': 20, 'value': 0}],
    'Enable endstops': [
        {'axis': 'x', 'num': 25, 'value': 0},
        {'axis': 'y', 'num': 26, 'value': 0},
        {'axis': 'z', 'num': 27, 'value': 0}],
    'Invert motor': [
        {'axis': 'x', 'num': 31, 'value': 0},
        {'axis': 'y', 'num': 32, 'value': 0},
        {'axis': 'z', 'num': 33, 'value': 0}],
    'Acceleration (steps)': [
        {'axis': 'x', 'num': 41, 'value': 500},
        {'axis': 'y', 'num': 42, 'value': 500},
        {'axis': 'z', 'num': 43, 'value': 500}],
    'Stop at home': [
        {'axis': 'x', 'num': 45, 'value': 0},
        {'axis': 'y', 'num': 46, 'value': 0},
        {'axis': 'z', 'num': 47, 'value': 0}],
    'Negatives only': [
        {'axis': 'x', 'num': 51, 'value': 0},
        {'axis': 'y', 'num': 52, 'value': 0},
        {'axis': 'z', 'num': 53, 'value': 0}],
    'Min speed (steps/s)': [
        {'axis': 'x', 'num': 61, 'value': 50},
        {'axis': 'y', 'num': 62, 'value': 50},
        {'axis': 'z', 'num': 63, 'value': 50}],
    'Max speed (steps/s)': [
        {'axis': 'x', 'num': 71, 'value': 800},
        {'axis': 'y', 'num': 72, 'value': 800},
        {'axis': 'z', 'num': 73, 'value': 800}],
    'Enable encoders': [
        {'axis': 'x', 'num': 101, 'value': 1},
        {'axis': 'y', 'num': 102, 'value': 1},
        {'axis': 'z', 'num': 103, 'value': 1}],
    'Encoder type': [
        {'axis': 'x', 'num': 105, 'value': 0},
        {'axis': 'y', 'num': 106, 'value': 0},
        {'axis': 'z', 'num': 107, 'value': 0}],
    'Missed steps': [
        {'axis': 'x', 'num': 111, 'value': 10},
        {'axis': 'y', 'num': 112, 'value': 10},
        {'axis': 'z', 'num': 113, 'value': 10}],
    'Encoder scaling': [
        {'axis': 'x', 'num': 115, 'value': 56},
        {'axis': 'y', 'num': 116, 'value': 56},
        {'axis': 'z', 'num': 117, 'value': 56}],
    'Decay (steps)': [
        {'axis': 'x', 'num': 121, 'value': 10},
        {'axis': 'y', 'num': 122, 'value': 10},
        {'axis': 'z', 'num': 123, 'value': 10}],
    'Use encoders for positioning': [
        {'axis': 'x', 'num': 125, 'value': 0},
        {'axis': 'y', 'num': 126, 'value': 0},
        {'axis': 'z', 'num': 127, 'value': 0}],
    'Invert encoders': [
        {'axis': 'x', 'num': 131, 'value': 0},
        {'axis': 'y', 'num': 132, 'value': 0},
        {'axis': 'z', 'num': 133, 'value': 0}],
    'Axis length (steps)': [
        {'axis': 'x', 'num': 141, 'value': 0},
        {'axis': 'y', 'num': 142, 'value': 0},
        {'axis': 'z', 'num': 143, 'value': 0}],
    'Stop at max': [
        {'axis': 'x', 'num': 145, 'value': 0},
        {'axis': 'y', 'num': 146, 'value': 0},
        {'axis': 'z', 'num': 147, 'value': 0}],
    'E-STOP on movement error': [
        {'axis': 'NA', 'num': 4, 'value': 0}],
    'Movement retries': [
        {'axis': 'NA', 'num': 5, 'value': 1}],
    'Second x-axis motor': [
        {'axis': 'X2', 'num': 36, 'value': 1},
        {'axis': 'X2 invert', 'num': 37, 'value': 1}],
    }

PARAMETER_SEEDS = [
    {'name': 'Movement timeout (seconds)', 'start_number': 11, 'value': 120},
    {'name': 'Keep motor active', 'start_number': 15, 'value': 0},
    {'name': 'Home at boot', 'start_number': 18, 'value': 0},
    {'name': 'Enable endstops', 'start_number': 25, 'value': 0},
    {'name': 'Invert motor', 'start_number': 31, 'value': 0},
    {'name': 'Acceleration (steps)', 'start_number': 41, 'value': 500},
    {'name': 'Stop at home', 'start_number': 45, 'value': 0},
    {'name': 'Negatives only', 'start_number': 51, 'value': 0},
    {'name': 'Min speed (steps/s)', 'start_number': 61, 'value': 50},
    {'name': 'Max speed (steps/s)', 'start_number': 71, 'value': 800},
    {'name': 'Enable encoders', 'start_number': 101, 'value': 1},
    {'name': 'Encoder type', 'start_number': 105, 'value': 0},
    {'name': 'Missed steps', 'start_number': 111, 'value': 10},
    {'name': 'Encoder scaling', 'start_number': 115, 'value': 56},
    {'name': 'Decay (steps)', 'start_number': 121, 'value': 10},
    {'name': 'Use encoders for positioning', 'start_number': 125, 'value': 0},
    {'name': 'Invert encoders', 'start_number': 131, 'value': 0},
    {'name': 'Axis length (steps)', 'start_number': 141, 'value': 0},
    {'name': 'Stop at max', 'start_number': 145, 'value': 0}
    ]

PARAMETER_SEEDLINGS = OrderedDict([
    ('Second x-axis motor', [
        {'num': 36, 'axis': 'X2', 'value': 1},
        {'num': 37, 'axis': 'X2 invert', 'value': 1}]),
    ('Movement retries', [
        {'num': 5, 'axis': 'NA', 'value': 1}]),
    ('E-STOP on movement error', [
        {'num': 4, 'axis': 'NA', 'value': 0}]),
    ])


class GenerateParameters(object):
    'Generate parameters table.'

    def __init__(self):
        self.parameters = PARAMETER_SEEDLINGS
        self.generate_parameters()

    def populate_parameter(self, name, start_number, value):
        'Populate x, y, and z parameters.'
        axes = []
        for i, axis in enumerate(['x', 'y', 'z']):
            axes.append(
                {'num': start_number + i, 'axis': axis, 'value': value}
                )
        self.parameters[name] = axes

    def generate_parameters(self):
        'Generate parameters dictionary.'
        for seed in PARAMETER_SEEDS[::-1]:
            self.populate_parameter(
                seed['name'], seed['start_number'], seed['value'])
        # Re-order
        self.parameters = OrderedDict(reversed(list(self.parameters.items())))
        # Adjustments
        # self.parameters['Invert encoders'][2]['value'] = 1

    def print_parameters(self):
        'Print generated parameters table.'
        # import json
        # print(json.dumps(self.parameters, indent=2))
        indent = ' ' * 4
        print('PARAMETERS = {')
        for name, params in self.parameters.items():
            print('{}\'{}\': ['.format(indent, name))
            for i, parameter in enumerate(params):
                print('{}{{'.format(indent * 2), end='')
                end = ','
                if i == len(params) - 1:
                    end = '],'
                for i, (label, value) in enumerate(sorted(parameter.items())):
                    comma = ', '
                    if i == len(parameter) - 1:
                        comma = ''
                    if isinstance(value, str):
                        value = '\'{}\''.format(value)
                    print('\'{}\': {}{}'.format(label, value, comma), end='')
                print('}}{}'.format(end))
        print('{}}}'.format(' ' * 4))


if __name__ == '__main__':
    GP = GenerateParameters()
    GP.print_parameters()
