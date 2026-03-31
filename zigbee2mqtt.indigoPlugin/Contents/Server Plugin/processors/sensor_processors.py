#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Sensor processor methods extracted from zigbeeHandler.py

from __future__ import annotations

from typing import Any, Dict

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import (
    DEBUG,
    INDIGO_ONE_SPACE_BEFORE_UNITS,
)


class SensorProcessorMixin:
    """Mixin class containing sensor processing methods (battery, humidity, illuminance, pressure, temperature, voltage)."""

    def process_property_battery(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "battery" not in json_payload:
                return
            if not zd_dev.pluginProps.get("SupportsBatteryLevel", False):
                return

            try:
                battery_level = int(json_payload["battery"])
            except TypeError:
                return
            except ValueError:
                try:
                    battery_level = int(float(json_payload["battery"]))
                except ValueError:
                    self.zigbeeLogger.warning(
                        f"Device '{zd_dev.name}' [{zd_dev.address}]: Invalid battery value '{json_payload['battery']}' (expected integer 0-100). Event ignored.")
                    return

            if zd_dev.states["batteryLevel"] != battery_level:
                self.key_value_lists[zd_dev.id].append({'key': 'batteryLevel', 'value': battery_level})
                self.zigbeeLogger.info(f"received \"{zd_dev.name}\" battery level {battery_level}%")
            else:
                if self.globals[DEBUG]:
                    self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged battery level: {battery_level}%")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)

    def process_property_humidity(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.pluginProps.get("uspHumidity", False) or "humidity" not in json_payload:
                return

            result = self.resolve_secondary_device(zd_dev, "Humidity", "secondaryDeviceHumiditySensor", "humidity")

            if not result.is_valid:
                self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Humidity event received but secondary device not found or not configured. Check device settings.")
                return

            if not result.device.enabled:
                return

            try:
                humidity = float(json_payload["humidity"])
            except ValueError:
                self.zigbeeLogger.warning(f"Device '{result.device.name}' [{zd_dev.address}]: Invalid humidity value '{json_payload['humidity']}' (expected numeric). Event ignored.")
                return

            if result.state_key not in result.device.states:
                self.zigbeeLogger.error(f"Device '{result.device.name}': State '{result.state_key}' not found. Device may need reconfiguration.")
                return

            decimal_places = self.get_decimal_places(zd_dev.pluginProps, "uspHumidityDecimalPlaces", zd_dev.name)
            humidity_value, ui_humidity_value = self.processDecimalPlaces(humidity, decimal_places, "%", INDIGO_ONE_SPACE_BEFORE_UNITS)

            state_image = indigo.kStateImageSel.HumiditySensor if result.is_secondary else None
            self.update_state_if_changed(
                result.device, result.state_key, humidity_value, ui_humidity_value,
                zd_dev, "hideHumidityBroadcast", "humidity level",
                state_image=state_image, compare_value=humidity
            )

        except Exception as exception_error:
            self.exception_handler(exception_error, True)

    def process_property_illuminance(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.pluginProps.get("uspIlluminance", False):
                return
            if "illuminance" not in json_payload and "illuminance_lux" not in json_payload:
                return

            result = self.resolve_secondary_device(zd_dev, "Illuminance", "secondaryDeviceIlluminanceSensor", "illuminance")

            raw_illuminance = json_payload.get("illuminance_lux", json_payload.get("illuminance"))

            if not result.is_valid:
                self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Illuminance event received but secondary device not found or not configured. Check device settings.")
                return

            if not result.device.enabled:
                return

            try:
                illuminance = float(json_payload.get("illuminance_lux", json_payload.get("illuminance")))
            except ValueError:
                self.zigbeeLogger.warning(f"Device '{result.device.name}' [{zd_dev.address}]: Invalid illuminance value '{raw_illuminance}' (expected numeric). Event ignored.")
                return

            if result.state_key not in result.device.states:
                self.zigbeeLogger.error(f"Device '{result.device.name}': State '{result.state_key}' not found. Device may need reconfiguration.")
                return

            decimal_places = self.get_decimal_places(zd_dev.pluginProps, "uspIlluminanceDecimalPlaces", zd_dev.name)
            illuminance_units_ui = zd_dev.pluginProps.get("uspIlluminanceUnits", "")
            illuminance_value, ui_illuminance_value = self.processDecimalPlaces(illuminance, decimal_places, illuminance_units_ui, INDIGO_ONE_SPACE_BEFORE_UNITS)

            state_image = indigo.kStateImageSel.LightSensor if result.is_secondary else None
            self.update_state_if_changed(
                result.device, result.state_key, illuminance_value, ui_illuminance_value,
                zd_dev, "hideIlluminanceBroadcast", "illuminance",
                state_image=state_image, compare_value=illuminance
            )

        except Exception as exception_error:
            self.exception_handler(exception_error, True)

    def process_property_pressure(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.pluginProps.get("uspPressure", False) or "pressure" not in json_payload:
                return

            result = self.resolve_secondary_device(zd_dev, "Pressure", "secondaryDevicePressureSensor", "pressure")

            if not result.is_valid:
                self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Pressure event received but secondary device not found or not configured. Check device settings.")
                return

            if not result.device.enabled:
                return

            try:
                pressure = float(json_payload["pressure"])
            except ValueError:
                self.zigbeeLogger.warning(f"Device '{result.device.name}' [{zd_dev.address}]: Invalid pressure value '{json_payload['pressure']}' (expected numeric). Event ignored.")
                return

            if result.state_key not in result.device.states:
                self.zigbeeLogger.error(f"Device '{result.device.name}': State '{result.state_key}' not found. Device may need reconfiguration.")
                return

            decimal_places = self.get_decimal_places(zd_dev.pluginProps, "uspPressureDecimalPlaces", zd_dev.name)
            pressure_units_ui = zd_dev.pluginProps.get("uspPressureUnits", "")
            pressure_value, ui_pressure_value = self.processDecimalPlaces(pressure, decimal_places, pressure_units_ui, INDIGO_ONE_SPACE_BEFORE_UNITS)

            self.update_state_if_changed(
                result.device, result.state_key, pressure_value, ui_pressure_value,
                zd_dev, "hidePressureBroadcast", "pressure level"
            )

        except Exception as exception_error:
            self.exception_handler(exception_error, True)

    def process_property_temperature(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.pluginProps.get("uspTemperature", False):
                return
            if "temperature" not in json_payload and "device_temperature" not in json_payload:
                return

            # Temperature has special handling: primary can use "sensorValue" or "temperature" state
            indigo_prop = zd_dev.pluginProps.get("uspTemperatureIndigo", "INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE")
            primary_state_key = "sensorValue" if indigo_prop == "INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE" else "temperature"

            result = self.resolve_secondary_device(zd_dev, "Temperature", "secondaryDeviceTemperatureSensor", primary_state_key)

            if not result.is_valid:
                self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Temperature event received but secondary device not found or not configured. Check device settings.")
                return

            if not result.device.enabled:
                return

            try:
                temperatureUnitsConversion = self.validate_temperature_conversion(zd_dev.pluginProps, zd_dev.name)
                temperature_unit_ui = "°C" if temperatureUnitsConversion in ["C", "F>C"] else "°F"

                raw_temp = json_payload.get("device_temperature", json_payload.get("temperature"))
                temperature = float(raw_temp)

                if temperatureUnitsConversion == "C>F":
                    temperature = float(((float(temperature) * 9) / 5) + 32.0)
                elif temperatureUnitsConversion == "F>C":
                    temperature = float(((float(temperature) - 32.0) * 5) / 9)
            except ValueError:
                temp_key = "device_temperature" if "device_temperature" in json_payload else "temperature"
                self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Invalid temperature value '{json_payload[temp_key]}' (expected numeric). Event ignored.")
                return

            if result.state_key not in result.device.states:
                self.zigbeeLogger.error(f"Device '{result.device.name}': State '{result.state_key}' not found. Device may need reconfiguration.")
                return

            decimal_places = self.get_decimal_places(zd_dev.pluginProps, "uspTemperatureDecimalPlaces", zd_dev.name)
            temperature_value, ui_temperature_value = self.processDecimalPlaces(temperature, decimal_places, temperature_unit_ui, INDIGO_ONE_SPACE_BEFORE_UNITS)

            state_image = indigo.kStateImageSel.TemperatureSensor if result.state_key == "sensorValue" else None
            self.update_state_if_changed(
                result.device, result.state_key, temperature_value, ui_temperature_value,
                zd_dev, "hideTemperatureBroadcast", "temperature",
                state_image=state_image
            )

        except Exception as exception_error:
            self.exception_handler(exception_error, True)

    def process_property_voltage(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.pluginProps.get("uspVoltage", False) or "voltage" not in json_payload:
                return

            result = self.resolve_secondary_device(zd_dev, "Voltage", "secondaryDeviceVoltageSensor", "voltage")

            if not result.is_valid:
                self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Voltage event received but secondary device not found or not configured. Check device settings.")
                return

            if not result.device.enabled:
                return

            try:
                if json_payload["voltage"] is None:
                    return
                voltage = float(json_payload["voltage"])
            except ValueError:
                self.zigbeeLogger.warning(f"Device '{result.device.name}' [{zd_dev.address}]: Invalid voltage value '{json_payload['voltage']}' (expected numeric). Event ignored.")
                return

            if result.state_key not in result.device.states:
                self.zigbeeLogger.error(f"Device '{result.device.name}': State '{result.state_key}' not found. Device may need reconfiguration.")
                return

            decimal_places = self.get_decimal_places(zd_dev.pluginProps, "uspVoltageDecimalPlaces", zd_dev.name)
            voltage_units_ui = zd_dev.pluginProps.get("uspVoltageUnits", "V")
            voltage_value, ui_voltage_value = self.processDecimalPlaces(voltage, decimal_places, voltage_units_ui, INDIGO_ONE_SPACE_BEFORE_UNITS)

            self.update_state_if_changed(
                result.device, result.state_key, voltage_value, ui_voltage_value,
                zd_dev, "hideVoltageBroadcast", "voltage"
            )

        except Exception as exception_error:
            self.exception_handler(exception_error, True)
