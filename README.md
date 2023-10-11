# Laser Targeting PoC

## Objective

Given a live capture from a webcam and frame coordinates, target a laser driven via either Helios or Either Dream 4 laser DAC to the given coordinates.

## Libraries

## Setup and run

C/C++ libraries included under `deps/` were compiled for osx-arm64 and linux-x86_64.

- Helios DAC: https://github.com/Grix/helios_dac
- Ether Dream 4 DAC: https://github.com/kogentech/ether-dream-sdk

To run the main app:

```
python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements.txt
python3 ./src/main.py
```
