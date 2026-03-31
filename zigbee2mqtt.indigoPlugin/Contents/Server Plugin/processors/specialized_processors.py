#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Specialized processor methods extracted from zigbeeHandler.py

from __future__ import annotations

import datetime
from typing import Any, Dict

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import (
    DEBUG,
    INDIGO_NO_SPACE_BEFORE_UNITS,
    INDIGO_ONE_SPACE_BEFORE_UNITS,
    INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE,
    ZD,
    ZD_PREVIOUS_POWER_LEVEL,
    ZD_PREVIOUS_POWER_LEVEL_LEFT,
    ZD_PREVIOUS_POWER_LEVEL_RIGHT,
)


class SpecializedProcessorMixin:
    """Mixin class containing specialized processing methods."""

    def process_property_energy(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "energy" in json_payload:
                if zd_dev.pluginProps.get("uspEnergy", False):
                    energy_units_ui = f" {zd_dev.pluginProps.get('uspEnergyUnits', '')}"
                    try:
                        energy = float(json_payload["energy"])
                    except ValueError:
                        return
                    if "accumEnergyTotal" in zd_dev.states:
                        decimal_places = self.get_decimal_places(zd_dev.pluginProps, "uspEnergyDecimalPlaces", zd_dev.name)
                        value, uiValue = self.processDecimalPlaces(energy, decimal_places, energy_units_ui, INDIGO_NO_SPACE_BEFORE_UNITS)
                        if zd_dev.states["accumEnergyTotal"] != value:  # noqa: reference before assignment
                            self.key_value_lists[zd_dev.id].append({'key': 'accumEnergyTotal', 'value': value, 'uiValue': uiValue})
                            if not bool(zd_dev.pluginProps.get("hideEnergyBroadcast", False)):
                                self.zigbeeLogger.info(f"received \"{zd_dev.name}\" accumulated energy total update to {uiValue}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_topic_last_seen(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return

            if "last_seen" in json_payload:
                valid = False
                try:
                    ts = int(json_payload["last_seen"]) / 1000
                    last_seen = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    valid = True
                except ValueError:
                    self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Invalid last_seen value '{json_payload['last_seen']}' (expected Unix timestamp). Event ignored.")
                if valid:
                    if "last_seen" in zd_dev.states:
                        if zd_dev.states["last_seen"] != last_seen:  # noqa: reference before assignment
                            self.key_value_lists[zd_dev.id].append({'key': 'last_seen', 'value': last_seen})
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" last seen {last_seen}")
                        else:
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged last seen {last_seen}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_link_quality(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "linkquality" in json_payload:
                if zd_dev.pluginProps.get("uspLinkQuality", False):
                    linkquality = json_payload["linkquality"]
                    self.key_value_lists[zd_dev.id].append({'key': 'linkQuality', 'value': linkquality})
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_power(self, zigbee_coordinator_ieee: str, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "power" in json_payload:
                if zd_dev.pluginProps.get("uspPower", False):

                    power_units_ui = f" {zd_dev.pluginProps.get('uspPowerUnits', '')}"
                    try:
                        power = float(json_payload["power"])
                    except ValueError:
                        return
                    minimumPowerLevel = self.get_float_config(zd_dev.pluginProps, "uspPowerMinimumReportingLevel", default=0.0, min_val=0.0, device_name=zd_dev.name)
                    reportingPowerHysteresis = self.validate_hysteresis(zd_dev.pluginProps, "uspPowerReportingHysteresis", default=6.0, device_name=zd_dev.name)
                    if reportingPowerHysteresis > 0.0:  # noqa [Duplicated code fragment!]
                        reportingPowerHysteresis = reportingPowerHysteresis / 2

                    previousPowerLevel = float(self.globals[ZD][zigbee_coordinator_ieee][zd_dev.address].get(ZD_PREVIOUS_POWER_LEVEL, float(zd_dev.states["curEnergyLevel"])))

                    # Determine if power state should be reported depending on hysteresis
                    report_power_state = False
                    power_variance_minimum = previousPowerLevel - reportingPowerHysteresis
                    power_variance_maximum = previousPowerLevel + reportingPowerHysteresis
                    if power_variance_minimum < 0.0:
                        power_variance_minimum = 0.0
                    if power >= minimumPowerLevel:
                        # power_variance_minimum = previousPowerLevel - powerReportingVariance
                        # power_variance_maximum = previousPowerLevel + powerReportingVariance
                        if power < power_variance_minimum or power > power_variance_maximum:
                            report_power_state = True
                    elif previousPowerLevel >= minimumPowerLevel:
                        if power < power_variance_minimum or power > power_variance_maximum:
                            report_power_state = True
                    if report_power_state:
                        self.globals[ZD][zigbee_coordinator_ieee][zd_dev.address][ZD_PREVIOUS_POWER_LEVEL] = power

                    decimal_places = self.get_decimal_places(zd_dev.pluginProps, "uspPowerDecimalPlaces", zd_dev.name)
                    value, uiValue = self.processDecimalPlaces(power, decimal_places, power_units_ui, INDIGO_NO_SPACE_BEFORE_UNITS)
                    self.key_value_lists[zd_dev.id].append({'key': 'curEnergyLevel', 'value': value, 'uiValue': uiValue})
                    if report_power_state:
                        if not bool(zd_dev.pluginProps.get("hidePowerBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" power update to {uiValue}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_power_left_right(self, zigbee_coordinator_ieee: str, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            power_process_list = list()

            if "power_left" in json_payload:
                if zd_dev.enabled:
                    power_process_list.append(("power_left", "Left", zd_dev, ZD_PREVIOUS_POWER_LEVEL_LEFT))
            if "power_right" in json_payload:
                zd_dev_secondary_id = zd_dev.pluginProps.get("secondaryDeviceMultiSocket", 0)  # Returns int zero if no secondary pressure device
                if zd_dev_secondary_id != 0:
                    zd_dev_secondary = indigo.devices[zd_dev_secondary_id]
                    if zd_dev_secondary.enabled:
                        power_process_list.append(("power_right", "Right", zd_dev_secondary, ZD_PREVIOUS_POWER_LEVEL_RIGHT))

            for json_payload_power_state, side, zd_dev_to_process, zd_previous_power_level_contant in power_process_list:
                if zd_dev.pluginProps.get(f"uspPower{side}", False):
                    usp_power_units = f"uspPower{side}Units"
                    power_units_ui = f" {zd_dev.pluginProps.get(usp_power_units, '')}"
                    try:
                        power = float(json_payload[json_payload_power_state])
                    except ValueError:
                        return
                    minimumPowerLevel = self.get_float_config(zd_dev.pluginProps, f"uspPower{side}MinimumReportingLevel", default=0.0, min_val=0.0, device_name=zd_dev.name)
                    reportingPowerHysteresis = self.validate_hysteresis(zd_dev.pluginProps, f"uspPower{side}ReportingHysteresis", default=6.0, device_name=zd_dev.name)
                    if reportingPowerHysteresis > 0.0:  # noqa [Duplicated code fragment!]
                        reportingPowerHysteresis = reportingPowerHysteresis / 2

                    previousPowerLevel = float(self.globals[ZD][zigbee_coordinator_ieee][zd_dev_to_process.address].get(zd_previous_power_level_contant, float(zd_dev_to_process.states["curEnergyLevel"])))

                    # Determine if power state should be reported depending on hysteresis
                    report_power_state = False
                    power_variance_minimum = previousPowerLevel - reportingPowerHysteresis
                    power_variance_maximum = previousPowerLevel + reportingPowerHysteresis
                    if power_variance_minimum < 0.0:
                        power_variance_minimum = 0.0
                    if power >= minimumPowerLevel:
                        # power_variance_minimum = previousPowerLevel - powerReportingVariance
                        # power_variance_maximum = previousPowerLevel + powerReportingVariance
                        if power < power_variance_minimum or power > power_variance_maximum:
                            report_power_state = True
                    elif previousPowerLevel >= minimumPowerLevel:
                        if power < power_variance_minimum or power > power_variance_maximum:
                            report_power_state = True
                    if report_power_state:
                        self.globals[ZD][zigbee_coordinator_ieee][zd_dev.address][zd_previous_power_level_contant] = power

                    decimal_places = self.get_decimal_places(zd_dev.pluginProps, f"uspPower{side}DecimalPlaces", zd_dev.name)
                    value, uiValue = self.processDecimalPlaces(power, decimal_places, power_units_ui, INDIGO_NO_SPACE_BEFORE_UNITS)
                    self.key_value_lists[zd_dev_to_process.id].append({'key': 'curEnergyLevel', 'value': value, 'uiValue': uiValue})
                    if report_power_state:
                        if not bool(zd_dev.pluginProps.get(f"hidePower{side}Broadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" power update to {uiValue}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_target_distance(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.pluginProps.get("uspTargetDistance", False) or "target_distance" not in json_payload:
                return
            if not zd_dev.enabled:
                return

            if json_payload["target_distance"] is None:
                return
            try:
                target_distance = float(json_payload["target_distance"])
            except (ValueError, TypeError):
                self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Invalid target_distance value '{json_payload['target_distance']}' (expected numeric). Event ignored.")
                return

            if "targetDistance" not in zd_dev.states:
                return

            decimal_places = self.get_decimal_places(zd_dev.pluginProps, "uspTargetDistanceDecimalPlaces", zd_dev.name)
            target_distance_units_ui = zd_dev.pluginProps.get("uspTargetDistanceUnits", "m")
            target_distance_value, ui_target_distance_value = self.processDecimalPlaces(target_distance, decimal_places, target_distance_units_ui, INDIGO_ONE_SPACE_BEFORE_UNITS)

            if zd_dev.states["targetDistance"] != target_distance_value:
                self.key_value_lists[zd_dev.id].append({'key': 'targetDistance', 'value': target_distance_value, 'uiValue': ui_target_distance_value})
                if not bool(zd_dev.pluginProps.get("hideTargetDistanceBroadcast", False)):
                    self.zigbeeLogger.info(f"received \"{zd_dev.name}\" target distance update to {ui_target_distance_value}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_radar(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            # Check for Radar [Presence & Presence Event] e.g. Aqara FP1
            if "presence" in json_payload and "presence_event" in json_payload:
                if zd_dev.pluginProps.get("uspPresence", False) and zd_dev.pluginProps.get("uspPresenceEvent", False):
                    try:
                        on_off_state = bool(json_payload["presence"])  # Can be null on Zigbee2mqtt startup
                    except ValueError:
                        on_off_state = False
                    presence = json_payload["presence"]
                    presence_event = json_payload["presence_event"]
                    if on_off_state == False:
                        if presence_event in ["enter", "left_enter", "right_enter", "approach"]:
                            on_off_state = True
                    on_off_state_ui = "on" if on_off_state == True else "off"
                    if (zd_dev.states["onOffState"] != on_off_state) or (zd_dev.states["presence"] != presence) or (zd_dev.states["presenceEvent"] != presence_event):
                        self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                        self.key_value_lists[zd_dev.id].append({'key': 'presence', 'value': presence})
                        self.key_value_lists[zd_dev.id].append({'key': 'presenceEvent', 'value': presence_event})
                        if not bool(zd_dev.pluginProps.get("hidePresenceBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" radar sensor '{on_off_state_ui}', presence '{presence}', presence event '{presence_event}'")

            # Check for just Presence
            elif "presence" in json_payload:
                if zd_dev.pluginProps.get("uspPresence", False):
                    try:
                        on_off_state = bool(json_payload["presence"])  # Can be null on Zigbee2mqtt startup
                    except ValueError:
                        on_off_state = False
                    presence = json_payload["presence"]
                    on_off_state_ui = "on" if on_off_state == True else "off"
                    if (zd_dev.states["onOffState"] != on_off_state) or (zd_dev.states["presence"] != presence):
                        self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                        self.key_value_lists[zd_dev.id].append({'key': 'presence', 'value': presence})
                        if not bool(zd_dev.pluginProps.get("hidePresenceBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" radar sensor '{on_off_state_ui}', presence '{presence}'")

            if "presence_detection_options" in json_payload:
                if zd_dev.pluginProps.get("uspPresenceDetectionOptions", False):
                    valid_values = {"both", "mmwave", "pir"}
                    presence_detection_options_state = (value if (value := json_payload.get("presence_detection_options")) in valid_values else "Unknown")

                    self.key_value_lists[zd_dev.id].append({'key': 'presenceDetectionOptions', 'value': presence_detection_options_state})

            if "pir_detection" in json_payload:
                if zd_dev.pluginProps.get("uspPirDetection", False):
                    try:
                        pir_detection_state = bool(json_payload["pir_detection"])  # Can be null on Zigbee2mqtt startup
                    except ValueError:
                        pir_detection_state = False
                    self.key_value_lists[zd_dev.id].append({'key': 'pirDetection', 'value': pir_detection_state})
                    if not bool(zd_dev.pluginProps.get("hidePirDetectionBroadcast", False)):
                        self.zigbeeLogger.info(f"received \"{zd_dev.name}\" PIR detection '{pir_detection_state}'")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_strength(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "strength" in json_payload:
                if zd_dev.pluginProps.get("uspStrength", False):
                    strength = json_payload["strength"]
                    # zd_dev.updateStateOnServer(key="action", value="")  # To force Indigo to recognise a state change

                    if strength != zd_dev.states["strength"]:
                        self.key_value_lists[zd_dev.id].append({"key": "strength", "value": strength})
                        if not bool(zd_dev.pluginProps.get("hideVibrationBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" vibration sensor strength '{strength}' event")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_tamper(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "tamper" in json_payload:
                if zd_dev.pluginProps.get("uspTamper", False):
                    tamper = False if json_payload["tamper"] == False else True
                    self.key_value_lists[zd_dev.id].append({'key': 'tamper', 'value': tamper})
                    if not bool(zd_dev.pluginProps.get("hideTamperBroadcast", False)):
                        self.zigbeeLogger.info(f"received \"{zd_dev.name}\" contact sensor {tamper} event")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_vibration(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "vibration" in json_payload:
                if zd_dev.pluginProps.get("uspVibration", False):
                    state_on_off_state = zd_dev.states["onOffState"]
                    state_action = zd_dev.states["action"]
                    on_off_state_ui = "on" if json_payload["vibration"] == True else "off"
                    on_off_state = json_payload["vibration"]
                    if (on_off_state and state_action == "idle") or ((not on_off_state) and state_action != "idle"):
                        self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                        if not on_off_state:  # i.e. "off"
                            self.key_value_lists[zd_dev.id].append({"key": "action", "value": "idle"})
                        if not bool(zd_dev.pluginProps.get("hideVibrationBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" vibration sensor '{on_off_state_ui}' event")
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
