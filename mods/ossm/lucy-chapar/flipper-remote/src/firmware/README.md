# Flipper firmware with the BLE central role

The OSSM is a Bluetooth peripheral, like the Flipper. To connect to it, the
Flipper has to act as a *central*. Stock Flipper firmware can't: it loads ST's
"Light" radio stack, which ST documents as "GAP peripheral only".

The official firmware already supports ST's "Full" stack as a build option
(`COPRO_STACK_TYPE=ble_full`). This patch switches to it and adds a small
central / GATT client API for apps.

## What the patch changes (against official 1.5.1)

| File | Change |
|---|---|
| `fbt_options.py` | Build with `stm32wb5x_BLE_Stack_full_fw.bin`, `COPRO_STACK_TYPE = "ble_full"` |
| `targets/f7/ble_glue/gap.c` | Init GAP as peripheral **and** central + observer when the Full stack is running |
| `targets/f7/ble_glue/furi_ble/central.{h,c}` | New: scan, connect, discover, read, write, subscribe. Events go to the app through a callback |
| `targets/f7/api_symbols.csv` | Exports `ble_central_*` to apps. API 88.2 to 88.3 |

Everything else (phone app pairing, BadUSB over BLE, the HID app) keeps
working: the peripheral role is untouched and the central code only claims
events for its own connection.

## Build

Use the official toolchain (fbt downloads it):

```
git clone --recursive --branch 1.5.1 https://github.com/flipperdevices/flipperzero-firmware
cd flipperzero-firmware
git apply /path/to/0001-ble-central-role.patch
cp -r /path/to/flipper_app applications_user/ossm_remote
./fbt COMPACT=1 DEBUG=0 updater_package
```

The update package ends up in `dist/f7-C/`. Install it with qFlipper
("Install from file", pick the `.tgz`) or copy the folder to the SD card's
`update/` directory and run it from the Flipper's file browser. The update
also flashes the Full radio stack, which takes a minute longer than usual.

The OSSM app gets built with it as `dist/f7-C/apps/Bluetooth/ossm_remote.fap`.

## Going back

Install any official release with qFlipper. It puts the Light stack back.

## Trade-offs

- The Full stack is about 36 KB bigger, so there is that much less flash for
  the firmware itself. 1.5.1 with `COMPACT=1` is expected to fit; a build that
  doesn't fit fails at link time rather than producing a broken image.
- Apps built for this firmware (API 88.3) won't load on stock firmware, and
  stock apps keep working here.
