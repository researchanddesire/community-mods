# Flipper firmware: flipper-ble-scanner (Momentum + ST Full radio stack)

The OSSM is a Bluetooth peripheral, like the Flipper. To connect to it, the
Flipper has to act as a *central*. Stock firmware can't: it loads ST's "Light"
radio stack, which ST documents as "GAP peripheral only".

This app runs on the firmware from
[elhenro/flipper-ble-scanner](https://github.com/elhenro/flipper-ble-scanner)
(GPL-3.0). That project:

- builds Momentum (pinned to dev `d3f89dfe`) with ST's **Full** BLE stack and
  matching option bytes (`ob_full.data`);
- turns on the observer and central roles in `gap.c` when the Full stack runs;
- exports `furi_hal_bt_start_scan`, `furi_hal_bt_stop_scan` and
  `furi_hal_bt_hci_command` (raw HCI/ACI) to apps. API 87.1 to 87.2.

The OSSM app needs nothing else from the firmware. Its GATT client
(`flipper_app/ossm_central.c`) is built on those three calls plus the existing
`ble_event_dispatcher` hooks. There is no firmware patch of our own.

## Build and flash (macOS or Linux, Flipper on USB, qFlipper closed)

```
git clone https://github.com/elhenro/flipper-ble-scanner
cd flipper-ble-scanner
git checkout 1d2564a                 # the version this app was written against
./build.sh fw                        # fetch Momentum, apply the patch, build
ln -s /path/to/src/flipper_app vendor/momentum/applications_user/ossm_remote
cd vendor/momentum
./fbt COPRO_STACK_TYPE=ble_full COPRO_STACK_BIN=stm32wb5x_BLE_Stack_full_fw.bin \
      COPRO_OB_DATA=../../ob_full.data updater_package fap_ossm_remote
cd ../..
./build.sh flash-fw                  # first time: installs the Full radio stack + firmware
```

Then install the app: from `vendor/momentum`, run
`./fbt COPRO_STACK_TYPE=ble_full COPRO_STACK_BIN=stm32wb5x_BLE_Stack_full_fw.bin COPRO_OB_DATA=../../ob_full.data launch APPSRC=applications_user/ossm_remote`.
It lands in **Apps > Bluetooth > OSSM Remote**.

If the updater stops at "Waiting for SD card" or "Manifest pointer error",
use `./build.sh flash-dfu` once the radio stack is already Full (see that
project's README). Check the stack with the CLI: `info device` should show
`radio.stack.type: 1`.

## Going back

Install official Momentum (or official firmware) with qFlipper or the web
updater. That restores the Light stack. A normal Momentum update also removes
the patch, so the OSSM app stops working until you reinstall this build.

## Trade-offs

- The Full stack is bigger, so there is less flash for the firmware itself.
- Apps built for this firmware (API 87.2) need its exports. On stock firmware
  the loader refuses the OSSM app.
