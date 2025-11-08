# Robot Hat

Robot Hat Python library for Raspberry Pi.

Quick Links:

- [Robot Hat](#robot-hat)
  - [About Robot Hat](#about-robot-hat)
  - [Update](#update)
  - [Installation](#installation)
  - [Trouble Shooting](#trouble-shooting)
  - [About SunFounder](#about-sunfounder)
  - [License](#license)
  - [Contact us](#contact-us)

## About Robot Hat

Robot HAT is a multifunctional expansion board that allows Raspberry Pi to be quickly turned into a robot. An MCU is on board to extend the PWM output and ADC input for the Raspberry Pi, as well as a motor driver chip, Bluetooth module, I2S audio module and mono speaker. As well as the GPIOs that lead out of the Raspberry Pi itself.

### TTS (Text-to-Speech) Features

The Robot Hat library includes an enhanced TTS system with the following capabilities:

- **Multiple TTS Engines**: Support for espeak, espeak-ng, and pico2wave
- **Enhanced Volume**: 2x volume boost for clearer audio output
- **No Message Repetition**: Fixed threading issues that caused duplicate speech
- **Thread-Safe Operations**: Proper speech queue management prevents conflicts
- **Blocking/Non-blocking Speech**: Choose whether to wait for speech completion
- **Volume Control**: Adjustable volume gain using `tts.volume()` method (default 2.0x for louder speech)

#### Quick TTS Example

```python
from robot_hat import TTS

# Initialize TTS with espeak-ng (recommended)
tts = TTS(engine=TTS.ESPEAK_NG)

# Simple speech
tts.say("Hello, Robot Hat!")

# Blocking speech (wait for completion)
tts.say("This message will complete before continuing", blocking=True)

# Adjust volume (1.0 = normal, 2.0 = double volume)
tts.volume(3.0)  # Even louder
tts.say("This will be very loud!")
```


## Update

2024-11-08:
- **TTS (Text-to-Speech) Improvements**:
  - Fixed message repetition bug in TTS system
  - Enhanced volume control with 2x default volume boost
  - Improved speech amplitude for clearer audio output
  - Added thread-safe speech queue management
  - Better support for espeak, espeak-ng, and pico2wave engines

2023-11-29:
- Add more about Robot HAT's Hardware Introduction

2022-08-26:
- New Release

## Installation

```bash
git clone https://github.com/sunfounder/robot-hat.git -b v2.0
cd robot-hat
sudo python3 setup.py install

```

## Trouble Shooting

----------------------------------------------

## About SunFounder

SunFounder is a technology company focused on Raspberry Pi and Arduino open source community development. Committed to the promotion of open source culture, we strives to bring the fun of electronics making to people all around the world and enable everyone to be a maker. Our products include learning kits, development boards, robots, sensor modules and development tools. In addition to high quality products, SunFounder also offers video tutorials to help you make your own project. If you have interest in open source or making something cool, welcome to join us!

----------------------------------------------

## License

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied wa rranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

{Repository Name} comes with ABSOLUTELY NO WARRANTY; for details run ./show w. This is free software, and you are welcome to redistribute it under certain conditions; run ./show c for details.

SunFounder, Inc., hereby disclaims all copyright interest in the program '{Repository Name}' (which makes passes at compilers).

Mike Huang, 21 August 2015

Mike Huang, Chief Executive Officer

Email: service@sunfounder.com, support@sunfounder.com

----------------------------------------------

## Contact us

website:
    www.sunfounder.com

E-mail:
    service@sunfounder.com, support@sunfounder.com
