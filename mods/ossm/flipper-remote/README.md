# OSSM Remote for Flipper Zero

A Flipper Zero app that drives a stock OSSM over Bluetooth, the way the RADR
remote does: start and pause, speed, depth, stroke, sensation, Stroke Engine
patterns, and a one-press emergency stop. Nothing to plug in.

![screens](img/screens.png)

## The one catch: it needs the BLE-scanner firmware on the Flipper

The OSSM is a Bluetooth *peripheral*: it advertises and waits for a remote to
connect. To connect to it, the Flipper must be a *central*. Stock Flipper
firmware ships ST's "Light" radio stack, which is peripheral-only, so it can't.

The app runs on the firmware from
[elhenro/flipper-ble-scanner](https://github.com/elhenro/flipper-ble-scanner):
Momentum built with ST's "Full" radio stack, which exports raw HCI access to
apps. The app's own GATT client (`src/flipper_app/ossm_central.c`) sits on top
of that, so there is no firmware patch here, and the OSSM firmware stays stock.

## Install

Flipper on USB, qFlipper closed, macOS or Linux. Full steps and how to go back:
[src/firmware/README.md](src/firmware/README.md). In short:

```
git clone https://github.com/elhenro/flipper-ble-scanner && cd flipper-ble-scanner
git checkout 1d2564a
./build.sh fw                         # Momentum + scanner patch + Full stack
cp -r <this folder>/src/flipper_app vendor/momentum/applications_user/ossm_remote
(cd vendor/momentum && ./fbt COPRO_STACK_TYPE=ble_full \
   COPRO_STACK_BIN=stm32wb5x_BLE_Stack_full_fw.bin COPRO_OB_DATA=../../ob_full.data \
   updater_package fap_ossm_remote)
./build.sh flash-fw                   # installs the Full radio stack + firmware
```

The app shows up under **Apps > Bluetooth > OSSM Remote**. The `flipper-remote`
workflow builds the same update package and uploads it as an artifact.

## Using it

1. Power the OSSM and open the app. It finds and connects to the OSSM by itself.
2. Pick **Patterns** (Stroke Engine) or **Simple** (Simple Penetration).
3. If the OSSM says *Knob to zero*, turn its speed knob all the way down (that's
   the OSSM's own preflight check).

| Button | Control screen |
|---|---|
| Up / Down | choose Speed, Depth, Stroke, Sensation, Pattern |
| Left / Right | adjust (hold to move in steps of 5) |
| OK | play / pause (resume ramps speed up over about a second) |
| **Back** | **STOP: speed 0 and the OSSM parks at its menu** |
| Hold Back | back to the mode picker |

## Safety

- Back is always an emergency stop on the control screen. It skips any queued
  commands and sends `set:speed:0` then `go:menu`.
- If the Bluetooth link drops (Flipper crash, out of range), the OSSM firmware
  ramps its speed to 0 by itself.
- Leaving the app sends speed 0, returns the OSSM to its menu and disconnects.

## Layout

```
src/flipper_app/    the FAP (C): ossm_remote.c (logic, input, ramped sending),
                    ossm_ble.c (OSSM link), ossm_central.c (BLE central over
                    the firmware's raw HCI calls), ossm_ui.c
src/firmware/       how to build and flash the BLE-scanner firmware with the app
src/tools/          icon generator and a PC renderer for every screen
docs/PROTOCOL.md    the OSSM Bluetooth protocol as the app uses it
```

## License

The app and tools here follow this repo's license map. The firmware it runs on
(flipper-ble-scanner, Momentum) is GPL-3.0 and is not included here.
