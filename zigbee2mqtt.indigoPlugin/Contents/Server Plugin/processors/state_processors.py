#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# State processor methods extracted from zigbeeHandler.py

from __future__ import annotations

from typing import Any, Dict

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import DEBUG


class StateProcessorMixin:
    """Mixin class containing state processing methods."""

    def process_property_contact(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "contact" in json_payload:
                if zd_dev.pluginProps.get("uspContact", False):
                    on_off_state = False if json_payload["contact"] == True else True
                    on_off_state_ui = "closed" if json_payload["contact"] == True else "open"
                    if zd_dev.states["onOffState"] != on_off_state:
                        self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                        if not bool(zd_dev.pluginProps.get("hideContactBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" contact sensor {on_off_state_ui} event")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_water_leak(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "water_leak" in json_payload:
                if zd_dev.pluginProps.get("uspWaterLeak", False):
                    on_off_state = json_payload["water_leak"]
                    on_off_state_ui = "leak detected" if on_off_state else "dry"
                    if zd_dev.states["onOffState"] != on_off_state:
                        self.key_value_lists[zd_dev.id].append(
                            {'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui}
                        )
                        if not bool(zd_dev.pluginProps.get("hideWaterLeakBroadcast", False)):
                            self.zigbeeLogger.info(
                                f"received \"{zd_dev.name}\" water leak sensor {on_off_state_ui} event"
                            )

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_multi_state(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if "state_l1" in json_payload and zd_dev.enabled:
                on_off_state = True if json_payload["state_l1"] == "ON" else False
                on_off_state_ui = "on" if on_off_state else "off"
                if (zd_dev.states["onOffState"] != on_off_state) or ("onOffState.ui" in zd_dev.states and (zd_dev.states["onOffState.ui"] != on_off_state_ui)):
                    self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                    if not bool(zd_dev.pluginProps.get(f"hideStateL1Broadcast", False)):
                        self.zigbeeLogger.info(f"received \"{zd_dev.name}\" state L1 [On|off] '{on_off_state_ui}' event")
                else:
                    if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged state L1 [On|off] {on_off_state_ui} event")

            elif zd_dev.deviceTypeId != "multiSwitch" and zd_dev.deviceTypeId != "switch":
                if "state_left" in json_payload and zd_dev.enabled:
                    on_off_state = True if json_payload["state_left"] == "ON" else False
                    on_off_state_ui = "on" if on_off_state else "off"
                    if (zd_dev.states["onOffState"] != on_off_state) or ("onOffState.ui" in zd_dev.states and (zd_dev.states["onOffState.ui"] != on_off_state_ui)):
                        self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                        if not bool(zd_dev.pluginProps.get(f"hideStateLeftBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" state Left [On|off] '{on_off_state_ui}' event")
                    else:
                        if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged state Left [On|off] {on_off_state_ui} event")

            # v Start of inline process_secondary_switches Function ....
            def process_secondary_switches(device_type: str, switch: str) -> None:
                try:
                    if device_type == "multiSocket":
                        secondary_device_id_property_key = "secondaryDeviceMultiSocket"
                    elif device_type == "multiSwitch":
                        if switch == "state_left":
                            secondary_device_id_property_key = "secondaryDeviceMultiSwitchLeft"
                        elif switch == "state_right":
                            secondary_device_id_property_key = "secondaryDeviceMultiSwitchRight"
                        else:
                            return
                    elif device_type == "switch":
                        if switch == "state_single":
                            secondary_device_id_property_key = "secondaryDeviceSwitchSingle"
                        else:
                            return
                    elif device_type == "multiDimmer":
                        secondary_device_id_property_key = f"secondaryDeviceMultiDimmer{switch}"
                    elif device_type == "multiOutlet":
                        secondary_device_id_property_key = f"secondaryDeviceMultiOutlet{switch}"
                    else:
                        return
                    secondary_dev_id = zd_dev.pluginProps.get(secondary_device_id_property_key, 0)
                    if secondary_dev_id == 0:
                        return
                    secondary_dev = indigo.devices[secondary_dev_id]
                    if not secondary_dev.enabled:
                        return
                    if switch == "state_right":
                        secondary_state_name = switch
                        secondary_state_name_ui = " Right"
                    elif switch == "state_left":
                        secondary_state_name = switch
                        secondary_state_name_ui = " Left"
                    elif switch == "state_single":
                        secondary_state_name = "state"
                        secondary_state_name_ui = ""
                    else:
                        secondary_state_name = f"state_l{switch}"
                        secondary_state_name_ui = f" L{switch}"
                    if secondary_state_name in json_payload:
                        on_off_state = True if json_payload[secondary_state_name] == "ON" else False
                        on_off_state_ui = "on" if on_off_state else "off"

                        if (secondary_dev.states["onOffState"] != on_off_state) or ("onOffState.ui" in secondary_dev.states and (secondary_dev.states["onOffState.ui"] != on_off_state_ui)):
                            self.key_value_lists[secondary_dev_id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                            broadcast_property_name = f"hideState{secondary_state_name_ui}Broadcast"
                            if not bool(zd_dev.pluginProps.get(broadcast_property_name, False)):
                                self.zigbeeLogger.info(f"received \"{secondary_dev.name}\" state{secondary_state_name_ui} [On|off] '{on_off_state_ui}' event")
                        else:
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{secondary_dev.name}\" unchanged state{secondary_state_name_ui} [On|off] {on_off_state_ui} event")

                except Exception as exception_error:
                    self.exception_handler(exception_error, True)  # Log error and display failing statement

            # ^ ... End of inline process_secondary_switches Function

            # v Start of inline process_secondary_dimmers Function ....
            def process_secondary_dimmers(device_type: str, dimmer: str) -> None:
                try:
                    if device_type == "multiDimmer":
                        secondary_device_id_property_key = f"secondaryDeviceMultiDimmer{dimmer}"
                    else:
                        return
                    secondary_dev_id = zd_dev.pluginProps.get(secondary_device_id_property_key, 0)
                    if secondary_dev_id == 0:
                        return
                    secondary_dev = indigo.devices[secondary_dev_id]
                    if not secondary_dev.enabled:
                        return
                    secondary_state_name = f"brightness_l{switch}"
                    secondary_state_name_ui = f" L{switch}"
                    if secondary_state_name in json_payload:
                        valid = False
                        try:
                            brightness_255 = json_payload[secondary_state_name]
                            if "state" in json_payload and json_payload["state"] == "OFF":
                                brightness_255 = 0
                            brightness_100 = int((brightness_255 / 255) * 100)
                            if brightness_100 >= 99:
                                brightness_100 = 100
                            brightness_100_ui = f"{brightness_100}"
                            valid = True
                        except ValueError:
                            self.zigbeeLogger.warning(f"Device '{secondary_dev.name}' [{zd_dev.address}]: Invalid brightness value '{json_payload['brightness']}' (expected integer 0-255). Event ignored.")
                        if valid:
                            if "brightnessLevel" in secondary_dev.states:
                                if secondary_dev.states["brightnessLevel"] != brightness_100:  # noqa: reference before assignment
                                    brighten_dim_ui = "set"
                                    if brightness_100 > 0:
                                        if brightness_100 > secondary_dev.brightness:
                                            brighten_dim_ui = "brighten"
                                        else:
                                            brighten_dim_ui = "dim"
                                    if brightness_100 > 0:
                                        secondary_dev.updateStateImageOnServer(indigo.kStateImageSel.DimmerOn)
                                    else:
                                        secondary_dev.updateStateImageOnServer(indigo.kStateImageSel.DimmerOff)
                                    self.key_value_lists[secondary_dev.id].append({'key': 'brightnessLevel', 'value': brightness_100, 'uiValue': brightness_100_ui})  # noqa: reference before assignment
                                    if bool(zd_dev.pluginProps.get("SupportsWhite", False)):
                                        self.key_value_lists[secondary_dev.id].append({'key': 'whiteLevel', 'value': brightness_100})  # noqa: reference before assignment

                                    if not bool(secondary_dev.pluginProps.get("hideDimmerBroadcast", False)):
                                        self.zigbeeLogger.info(f"received {brighten_dim_ui} \"{secondary_dev.name}\" to brightness level {brightness_100_ui}")
                                else:
                                    if not bool(secondary_dev.pluginProps.get("hideDimmerBroadcast", False)):
                                        if self.globals[DEBUG]: self.zigbeeLogger.info(
                                            f"received \"{secondary_dev.name}\" unchanged brightness level {brightness_100_ui}")  # noqa: reference before assignment
                            else:
                                self.zigbeeLogger.error(f"Device '{secondary_dev.name}': State 'brightnessLevel' not found. Device may need reconfiguration.")  # noqa: reference before assignment

                except Exception as exception_error:
                    self.exception_handler(exception_error, True)  # Log error and display failing statement

            # ^ ... End of inline process_secondary_dimmers Function

            if zd_dev.deviceTypeId == "multiSocket":
                process_secondary_switches(zd_dev.deviceTypeId, "state_right")  # Inline 'def', see above
            elif zd_dev.deviceTypeId == "multiSwitch":
                process_secondary_switches(zd_dev.deviceTypeId, "state_right")  # Inline 'def', see above
                process_secondary_switches(zd_dev.deviceTypeId, "state_left")  # Inline 'def', see above
            elif zd_dev.deviceTypeId == "switch":
                process_secondary_switches(zd_dev.deviceTypeId, "state_single")  # Inline 'def', see above
            elif zd_dev.deviceTypeId == "multiDimmer":
                for switch in ["2", "3"]:
                    process_secondary_switches(zd_dev.deviceTypeId, switch)  # Inline 'def', see above
                    process_secondary_dimmers(zd_dev.deviceTypeId, switch)  # Inline 'def', see above
            elif zd_dev.deviceTypeId == "multiOutlet":
                for switch in ["2", "3", "4", "5"]:
                    process_secondary_switches(zd_dev.deviceTypeId, switch)  # Inline 'def', see above

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_occupancy(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "occupancy" in json_payload:
                if zd_dev.pluginProps.get("uspOccupancy", False):
                    on_off_state_ui = "on" if json_payload["occupancy"] == True else "off"
                    on_off_state = json_payload["occupancy"]
                    if zd_dev.states["onOffState"] != on_off_state:
                        self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                        if not bool(zd_dev.pluginProps.get("hideMotionBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" motion sensor '{on_off_state_ui}' event")
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_state(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "state" in json_payload:
                if zd_dev.deviceTypeId in ("outlet", "dimmer", "switch", "zigbeeGroupRelay", "zigbeeGroupDimmer"):
                    if zd_dev.pluginProps.get("uspOnOff", False):
                        on_off_state = True if json_payload["state"] == "ON" else False
                        on_off_state_ui = "on" if on_off_state else "off"
                        if (zd_dev.states["onOffState"] != on_off_state) or ("onOffState.ui" in zd_dev.states and (zd_dev.states["onOffState.ui"] != on_off_state_ui)):
                            self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                            if not bool(zd_dev.pluginProps.get("hideStateBroadcast", False)):
                                self.zigbeeLogger.info(f"received \"{zd_dev.name}\" state [On|off] '{on_off_state_ui}' event")
                            if zd_dev.deviceTypeId == "dimmer" or zd_dev.deviceTypeId == "zigbeeGroupDimmer":
                                if on_off_state:
                                    zd_dev.updateStateImageOnServer(indigo.kStateImageSel.DimmerOn)
                                else:
                                    zd_dev.updateStateImageOnServer(indigo.kStateImageSel.DimmerOff)
                                    brightness_level_ui = "0"
                                    self.key_value_lists[zd_dev.id].append({'key': 'brightnessLevel', 'value': 0, 'uiValue': brightness_level_ui})
                                    if bool(zd_dev.pluginProps.get("SupportsWhite", False)):
                                        self.key_value_lists[zd_dev.id].append({'key': 'whiteLevel', 'value': 0})
                        else:
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged state [On|off] {on_off_state_ui} event")

        except Exception as exception_error:
            # error_message = f"{exception_error}, Payload:{json_payload}"
            self.exception_handler(exception_error, True)  # Log error and display failing statement
