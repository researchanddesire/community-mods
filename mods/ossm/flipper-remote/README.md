# OSSM Remote for Flipper Zero

A Flipper Zero app that drives a stock OSSM over Bluetooth, the way the RADR
remote does: start and pause, speed, depth, stroke, sensation, Stroke Engine
patterns, and a one-press emergency stop. Nothing to plug in.

![screens](img/screens.png)

## The one catch: it needs a patched Flipper firmware

The OSSM is a Bluetooth *peripheral*: it advertises and waits for a remote to
connect. To connect to it, the Flipper must be a *central*. Stock Flipper
firmware ships ST's "Light" radio stack, which is peripheral-only, so it can't.

`src/firmware/` has a small patch for official Flipper firmware 1.5.1 that
switches to ST's "Full" stack (already a supported build option) and adds a
central / GATT-client API for apps. The OSSM firmware stays stock. Details and
build steps: [src/firmware/README.md](src/firmware/README.md).

On stock Flipper firmware the app opens but shows "Update your Flipper".

## Install

1. Build the update package (below) or download it from the
   `flipper-remote` workflow run's artifacts.
2. Install it with qFlipper ("Install from file", pick the `.tgz`).
3. The app is included: **Apps > Bluetooth > OSSM Remote**.

Build from this folder:

```
git clone --recursive --branch 1.5.1 https://github.com/flipperdevices/flipperzero-firmware fw
cd fw
git apply ../src/firmware/0001-ble-central-role.patch
cp -r ../src/flipper_app applications_user/ossm_remote
./fbt COMPACT=1 DEBUG=0 updater_package     # dist/f7-C/*.tgz
```

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
                    ossm_ble.c (scan, connect, discover, commands), ossm_ui.c
src/firmware/       patch for official Flipper firmware 1.5.1 (BLE central role)
src/tools/          icon generator and a PC renderer for every screen
docs/PROTOCOL.md    the OSSM Bluetooth protocol as the app uses it
```

## License

The app and tools are MPL 2.0 like other software in this repo. The firmware
patch modifies the Flipper Zero firmware, which is GPL-3.0, so the patch and
any firmware built with it are GPL-3.0.
