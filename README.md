# Laser Targeting PoC

## Objective

Given a live capture from a webcam and frame coordinates, target a laser driven via either Helios or Either Dream 4 laser DAC to the given coordinates.

## Libraries

C/C++ libraries included under `deps/` were compiled for osx-arm64 and linux-x86_64.

- Helios DAC: https://github.com/Grix/helios_dac
- Ether Dream 4 DAC: https://github.com/kogentech/ether-dream-sdk

## Helios DAC on Linux

Linux systems require udev rules to allow access to USB devices without root privileges.

1. Create a file *heliosdac.rules* in /etc/udev with the contents:

        ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1209", ATTRS{idProduct}=="e500", MODE="0660", GROUP="plugdev"

1. Create a link in /etc/udev/rules.d to *heliosdac.rules*:

		cd /etc/udev/rules.d
		sudo ln -s /etc/udev/heliosdac.rules 011_heliosdac.rules
	
1. Make sure the user account communicating with the DAC is in the *plugdev* group. On a Raspberry Pi, the "pi" user is in the *plugdev* group by default.

1. Issue the command `sudo udevadm control --reload` (or restart the computer).

## Run locally

To run the main app:

    python3 -m venv venv
    . venv/bin/activate
    pip3 install -r requirements.txt
    python3 ./src/main.py
