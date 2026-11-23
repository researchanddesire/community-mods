# How the app talks to the OSSM

Exactly what RADR does, over Bluetooth LE, with the Flipper as the central.

1. Scan for the service `522b443a-4f53-534d-0001-420badbabe69`.
2. Connect, ask for a bigger MTU.
3. Find these characteristics (UUID `522b443a-4f53-534d-XXXX-420badbabe69`):

| XXXX | Name | Use |
|---|---|---|
| `1000` | Command | write without response: `set:speed:0-100`, `set:stroke:`, `set:depth:`, `set:sensation:`, `set:pattern:0-6`, `go:strokeEngine`, `go:simplePenetration`, `go:menu` |
| `1010` | Speed knob config | write `false` so Bluetooth speed is independent of the knob |
| `2000` | State | notify + read, JSON `{"state":"strokeEngine.idle","speed":..,"stroke":..,"depth":..,"sensation":..,"pattern":..}` |
| `3000` | Patterns | read, JSON `[{"name":"Simple Stroke","idx":0},...]` |

4. Subscribe to State (CCCD is the handle after the value). If a notification
   is cut short by the MTU, read the whole value.
5. Read State and Patterns once, then send commands as the user acts.

Emergency stop is `set:speed:0` followed by `go:menu`. If the Bluetooth link
drops, the OSSM firmware ramps its speed to 0 by itself.
