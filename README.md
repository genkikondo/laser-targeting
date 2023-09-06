# Laser Targeting PoC

## Objective

Given a live capture from a webcam and frame coordinates, target a laser driven via either Helios or Either Dream 4 laser DAC to the given coordinates.

## Setup and run

Note: C++ libraries included were compiled for macos-arm64

```
python3 -m venv venv
. venv/bin/activate
pip3 install -r requirements.txt
python3 ./src/main.py
```
