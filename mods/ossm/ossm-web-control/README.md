# OSSM Web Control

[OSSM Web Control](https://ossm-web.forestpuppy.pet/), by
[ReadieFur](https://github.com/ReadieFur), puts OSSM controls on your phone,
tablet, or desktop through Bluetooth. Open it in a compatible browser, or
install it as an app for offline use on supported devices.

![OSSM Web Control landscape controls preview](https://raw.githubusercontent.com/ReadieFur/OSSM-Web-Control/main/docs/iPhone_Landscape.gif)

## More than a speed slider

- **Set both ends of the stroke.** A dual-handle range slider lets you adjust
  the start and end positions together with stroke length and depth.
- **Adjust speed and sensation separately.** Drag the sliders or use the
  numeric step controls for finer changes. Sensation changes the character of
  the selected pattern; patterns that support it also offer an invert control.
- **Rotate your phone.** The interface switches between portrait and landscape
  layouts, with controls arranged for the available screen space.
- **See the machine's state.** The interface shows ready, calibrating,
  reconnecting, and emergency-stop states, and disables motion controls while
  the machine is not ready.
- **Stop and recalibrate from the interface.** A stop tap sends a zero-speed
  command; a rapid second tap sends an emergency-stop command. Recalibration
  re-homes the rail and is required to resume after an emergency stop.

## Patterns and sensation

The app reads the available patterns from your OSSM and shows their descriptions.
For the standard patterns, it adds explanations of what sensation does:

| Pattern | What changes |
| --- | --- |
| Simple Stroke | A stroke with acceleration, coasting, and deceleration; no sensation setting. |
| Teasing Pounding | Sensation adjusts how strongly the motion favors one direction, with an invert option. |
| Robo Stroke | Sensation adjusts motion smoothing for a more robotic or smoother stroke. |
| Half'n'Half | Alternates full and half-depth strokes; sensation adjusts the difference. |
| Deeper | Builds to deeper strokes over successive cycles; sensation adjusts the cycle count before restarting. |
| Stop'n'Go | Pauses between strokes; sensation adjusts the pause duration. |
| Insist | Varies stroke length while maintaining speed. |

## Phone, desktop, and offline use

Requires **OSSM firmware v1.0.50 or newer** and Bluetooth support.

| Device | Browser |
| --- | --- |
| Desktop | Chromium-based browsers such as Chrome, Edge, or Brave |
| Android | Google Chrome |
| iPhone | [Bluefy Browser](https://apps.apple.com/us/app/bluefy-web-ble-browser/id1492822055) |

[Open the app](https://ossm-web.forestpuppy.pet/), choose **Connect OSSM**, and
select your device in the Bluetooth prompt. On supported devices, install it
as a progressive web app for offline use. Firmware updates are available through
the [official OSSM Web Flasher](https://docs.researchanddesire.com/ossm/tools/web-flasher).

More animated previews:
[desktop speed and range](https://raw.githubusercontent.com/ReadieFur/OSSM-Web-Control/main/docs/Live00000409_V1-0001.gif) ·
[desktop patterns](https://raw.githubusercontent.com/ReadieFur/OSSM-Web-Control/main/docs/Live00001607_V1-0002.gif) ·
[phone portrait](https://raw.githubusercontent.com/ReadieFur/OSSM-Web-Control/main/docs/iPhone_Portrait.gif).

## What's planned

The roadmap includes **absolute positioning**, **remote session sharing**, and
**external app syncing**, such as VRChat integration. These are planned features.

## Source and contributing

The app is open source under
[GPL-3.0-only](https://github.com/ReadieFur/OSSM-Web-Control/blob/main/LICENSE).
[Source, setup instructions, and app issues](https://github.com/ReadieFur/OSSM-Web-Control)
live in ReadieFur's repository. It uses the separate
[OSSM-BLE-Web](https://github.com/ReadieFur/OSSM-BLE-Web) library for Bluetooth
communication; connection-specific issues belong there. Contributions and
feedback are welcome upstream.

## Safety

BLE controls command real motion. Use at your own risk; verify stop behavior
and motion limits before use, and keep a physical way to stop the machine
within reach.
