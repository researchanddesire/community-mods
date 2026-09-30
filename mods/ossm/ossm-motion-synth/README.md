# OSSM Motion Synth

A patchable motion instrument by Lucy Chapar. Shape a waveform, patch an LFO or
attack/release envelope into rate, stroke, center or position, and hear the
signal with the optional audio preview.

**[Try it in your browser](https://lucychapar.com/ossm-motion-synth/)** ·
**[Source and setup](https://github.com/lucy-chapar/ossm-motion-synth)**

Use desktop Chrome or Edge for direct USB–RS485 control through Web Serial.
Wave shaping and audio also work without an adapter. No Raspberry Pi, firmware
flash or local app is required for the website edition; an optional Python
bridge is available in the source repository.

## Connect a motor

With power off, disconnect the 4-pin signal cable that runs to the OSSM
motherboard. This setup only needs 24 V power and USB–RS485 wired directly to
the motor.

In **Motor connection**, click **Connect** and choose the adapter, then
**Home → Arm → Run**. Sensorless homing measures both ends of the rail and
parks at center. See the upstream
[guide](https://github.com/lucy-chapar/ossm-motion-synth/blob/main/docs/GUIDE.md)
for setup and controls.

The browser runtime and simulated serial rail have automated tests; physical
motor validation of this browser edition is pending. Software Stop does not
replace physical power isolation.

## Source and license

This hub entry links to the independently maintained
[ossm-motion-synth repository](https://github.com/lucy-chapar/ossm-motion-synth).
The project uses **MPL-2.0**; source, documentation and license terms stay
upstream.
