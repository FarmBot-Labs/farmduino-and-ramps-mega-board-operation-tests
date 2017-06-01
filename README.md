# Farmduino and RAMPS/MEGA Board Operation Tests

Simple test suite for Farmduino and RAMPS/MEGA electronics boards

Requires [farmbot-arduino-firmware](https://github.com/FarmBot/farmbot-arduino-firmware)

## Setup

```
pip install -r requirements.txt
python electronics_test.py
```

## Test Suite Run Mode Options

### 1: Full output, prompt before each test

```
Turn pin 13 on:
begin test?
```

Press `<Enter>`

```
SENDING:   F41 P13 V1 M0
SENDING:   F42 P13 M0
RECEIVED:  R41 P13 V1 Q0
VALUE(S):  P13 V1
EXPECTED:  P13 V1
RESULT:    PASS
```

```
Move X axis forward:
begin test?
```

Press `<Enter>`

```
SENDING:   G00 X200 Y0 Z0
Motor:
  RECEIVED:  R82 X200 Y0 Z0 Q0
  VALUE(S):  X200 Y0 Z0
  EXPECTED:  X200 Y0 Z0
  RESULT:    PASS

Encoder:
  RECEIVED:  R82 X199 Y0 Z0 Q0
  VALUE(S):  X199 Y0 Z0
  EXPECTED:  X200 Y0 Z0
  RESULT:    PASS
```

### 2: Full output, no prompts

```
Turn pin 13 on:
SENDING:   F41 P13 V1 M0
SENDING:   F42 P13 M0
RECEIVED:  R41 P13 V1 Q0
VALUE(S):  P13 V1
EXPECTED:  P13 V1
RESULT:    PASS

...

Move X axis forward:
SENDING:   G00 X200 Y0 Z0
Motor:
  RECEIVED:  R82 X200 Y0 Z0 Q0
  VALUE(S):  X200 Y0 Z0
  EXPECTED:  X200 Y0 Z0
  RESULT:    PASS

Encoder:
  RECEIVED:  R84 X0 Y0 Z0 Q0
  VALUE(S):  X0 Y0 Z0
  EXPECTED:  X200 Y0 Z0
  RESULT:    FAIL
```

### 3: Show details only for failed tests, no prompts

```
Turn pin 13 on: PASS

...

Move X axis forward:
SENDING:   G00 X200 Y0 Z0
Motor: PASS
Encoder:
  SENT:      G00 X200 Y0 Z0
  RECEIVED:  R84 X0 Y0 Z0 Q0
  VALUE(S):  X0 Y0 Z0
  EXPECTED:  X200 Y0 Z0
  RESULT:    FAIL
```
