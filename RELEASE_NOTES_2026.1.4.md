# Zigbee2mqtt Bridge — Release 2026.1.4

This release rolls up all the work done since **2026.1.0** (the previous published build). Versions 2026.1.2 and 2026.1.3 were never published to GitHub, so their changes are included here too. There was no 2026.1.1.

> **Action required after updating:** this release upgrades the bundled MQTT library to a new major version. Simply reload the plugin from the Indigo **Plugins ▸ Reload** menu after installing. No device reconfiguration is needed.

---

## Highlights

- **More reliable MQTT connections.** The plugin now actively supervises the broker connection and automatically reconnects if it drops or stalls — no more needing to reload the plugin after a broker or network blip.
- **Upgraded MQTT engine.** Moved to paho-mqtt 2.1.0 for ongoing compatibility and bug fixes.
- **No more log spam from "null" sensor readings.** Devices that occasionally report empty/`null` values (common right after a Zigbee2mqtt restart) no longer flood the Indigo log with errors.

---

## New & Improved

### MQTT reliability
- Added a connection **supervisor** that detects a dropped or wedged broker connection and forces a reconnect automatically, with clear status messages in the log.
- Added reconnect backoff (retries ramp from 1 up to 60 seconds) so a broker outage no longer hammers the network.
- **Commands are no longer lost silently.** If the broker is disconnected when you try to control a device, the plugin now logs a clear warning that the command was dropped, and reports any publish failures, instead of failing quietly.
- Upgraded the bundled **paho-mqtt** library from 1.6.1 to **2.1.0**.

### Devices
- **Illuminance** can now be split out to a secondary Indigo device for **Presence** and **Radar** sensors (previously only temperature/humidity/voltage could be).
- Fixed secondary devices being incorrectly registered internally, which could cause inconsistent device tracking.

### Stability & log noise
- Fixed crashes and repeated log errors when a device publishes a numeric field (energy, power, humidity, temperature, pressure, brightness, colour temperature, blind position, etc.) as an empty/`null` value. These readings are now safely ignored.
  (Resolves [issue #3](https://github.com/autolog/Zigbee2mqtt_Bridge/issues/3).)
- Clearer MQTT disconnection messages in the Indigo log, including the underlying reason code.
- Log entries are now grouped under clearer `Zigbee2mqtt` logger names.

### Under the hood
- Major internal refactor: the main plugin file was reduced from ~4,000 lines to ~230 by consolidating all logic into focused modules. No change in behaviour — this makes future maintenance and fixes faster and safer.
- Config dialog robustness improvements, including back-compatibility for devices saved by older plugin versions.
- Removed an unused "Target Distance" device state.

---

## Compatibility

- **Indigo:** Server API 3.4
- **Python:** 3.10+
- Tested on Indigo 2025.2 with Python 3.13

---

## Version history covered by this release

| Version | Status | Summary |
|---------|--------|---------|
| 2026.1.4 | this release | Null-payload crash/log-spam fix ([#3](https://github.com/autolog/Zigbee2mqtt_Bridge/issues/3)) |
| 2026.1.3 | unpublished | Clearer MQTT disconnect log messages |
| 2026.1.2 | unpublished | paho-mqtt 2.1.0 upgrade, connection supervisor/auto-reconnect, secondary-device fixes, internal refactor |
| 2026.1.0 | previously published | — |
