#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Dimmer processor methods extracted from zigbeeHandler.py

from __future__ import annotations

import colorsys
import json
from typing import Any, Dict

try:
    from colormath.color_objects import XYZColor, sRGBColor, xyYColor
    from colormath.color_conversions import convert_color
except ImportError:
    pass

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import DEBUG


class DimmerProcessorMixin:
    """Mixin class containing dimmer processing methods."""

    def process_property_brightness(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "brightness" in json_payload:
                valid = False
                try:
                    brightness_255 = json_payload["brightness"]
                    if "state" in json_payload and json_payload["state"] == "OFF":
                        brightness_255 = 0
                    brightness_100 = int((brightness_255 / 255) * 100)
                    if brightness_100 >= 99:
                        brightness_100 = 100
                    brightness_100_ui = f"{brightness_100}"
                    valid = True
                except ValueError:
                    self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Invalid brightness value '{json_payload['brightness']}' (expected integer 0-255). Event ignored.")
                if valid:
                    if "brightnessLevel" in zd_dev.states:
                        if zd_dev.states["brightnessLevel"] != brightness_100:  # noqa: reference before assignment
                            brighten_dim_ui = "set"
                            if brightness_100 > 0:
                                if brightness_100 > zd_dev.brightness:
                                    brighten_dim_ui = "brighten"
                                else:
                                    brighten_dim_ui = "dim"

                            if brightness_100 > 0:
                                zd_dev.updateStateImageOnServer(indigo.kStateImageSel.DimmerOn)
                            else:
                                zd_dev.updateStateImageOnServer(indigo.kStateImageSel.DimmerOff)
                            self.key_value_lists[zd_dev.id].append({'key': 'brightnessLevel', 'value': brightness_100, 'uiValue': brightness_100_ui})  # noqa: reference before assignment
                            if bool(zd_dev.pluginProps.get("SupportsWhite", False)):
                                self.key_value_lists[zd_dev.id].append({'key': 'whiteLevel', 'value': brightness_100})  # noqa: reference before assignment

                            if not bool(zd_dev.pluginProps.get("hideDimmerBroadcast", False)):
                                self.zigbeeLogger.info(f"received {brighten_dim_ui} \"{zd_dev.name}\" to brightness level {brightness_100_ui}")
                        else:
                            if not bool(zd_dev.pluginProps.get("hideDimmerBroadcast", False)):
                                if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged brightness level {brightness_100_ui}")  # noqa: reference before assignment
                    else:
                        self.zigbeeLogger.error(f"Device '{zd_dev.name}': State 'brightnessLevel' not found. Device may need reconfiguration.")  # noqa: reference before assignment

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_color(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if ("color_mode" in json_payload and json_payload["color_mode"] != "color_temp") and "color" in json_payload and "brightness" in json_payload:
                valid = False
                color_mode = json_payload["color_mode"]
                x = 0.0
                y = 0.0
                try:
                    brightness = int(json_payload["brightness"])
                    if color_mode == "xy":
                        x = json_payload["color"]["x"]
                        y = json_payload["color"]["y"]
                        valid = True
                    elif "hue" in json_payload["color"] and "saturation" in json_payload["color"]:
                        hue = int(json_payload["color"]["hue"])
                        saturation = int(json_payload["color"]["saturation"])
                        valid = True
                    else:
                        self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Unknown color format in payload (expected 'xy' or 'hue/saturation'). Event ignored.")
                except ValueError:
                    self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Invalid color values (expected numeric brightness/hue/saturation). Event ignored.")
                if valid:
                    try:
                        if color_mode == "xy":
                            # convert x and y to RGB Start . . .
                            z_value = 1.0
                            observer_value = '10'
                            xyz_color = xyYColor(x, y, z_value, observer=observer_value)
                            rgb = convert_color(xyz_color, sRGBColor)
                            rgb_tuple = rgb.get_value_tuple()

                            rgb_tuple_red = rgb_tuple[0]
                            rgb_tuple_green = rgb_tuple[1]
                            rgb_tuple_blue = rgb_tuple[2]

                            if rgb_tuple_red > 1.0:
                                rgb_tuple_red = 1.0
                            if rgb_tuple_green > 1.0:
                                rgb_tuple_green = 1.0
                            if rgb_tuple_blue > 1.0:
                                rgb_tuple_blue = 1.0

                            # native_red = rgb_tuple_red * 255
                            # native_green = rgb_tuple_green * 255
                            # native_blue = rgb_tuple_blue * 255

                            # Convert to Indigo RGB values (0 - 100)
                            red = int(rgb_tuple_red * 100)
                            green = int(rgb_tuple_green * 100)
                            blue = int(rgb_tuple_blue * 100)

                            # . . . convert x and y to RGB End
                        else:
                            hue_for_colorsys = float(hue) / 360.0  # noqa: reference before assignment
                            saturation_for_colorsys = float(saturation) / 255.0  # noqa: reference before assignment
                            value_for_colorsys = float(brightness) / 255.0  # noqa: reference before assignment
                            red, green, blue = colorsys.hsv_to_rgb(hue_for_colorsys, saturation_for_colorsys, value_for_colorsys)
                            red = int(red * 100.0)
                            green = int(green * 100.0)
                            blue = int(blue * 100.0)
                    except Exception:  # noqa: too wide exception
                        return

                    self.key_value_lists[zd_dev.id].append({"key": "redLevel", "value": red})
                    self.key_value_lists[zd_dev.id].append({"key": "greenLevel", "value": green})
                    self.key_value_lists[zd_dev.id].append({"key": "blueLevel", "value": blue})

                    if (zd_dev.states["redLevel"] != red or
                        zd_dev.states["greenLevel"] != green or
                        zd_dev.states["blueLevel"] != blue):  # noqa: reference before assignment

                        self.key_value_lists[zd_dev.id].append({"key": "redLevel", "value": red})
                        self.key_value_lists[zd_dev.id].append({"key": "greenLevel", "value": green})
                        self.key_value_lists[zd_dev.id].append({"key": "blueLevel", "value": blue})
                        if not bool(zd_dev.pluginProps.get("hideDimmerBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" color update of R={red}%, G={green}%, B={blue}%")
                            # self.zigbeeLogger.info(f"previous \"{zd_dev.name}\" color values were R={int(zd_dev.states['redLevel'])}%, G={int(zd_dev.states['greenLevel'])}%, B={int(zd_dev.states['blueLevel'])}%")
                    else:
                        if not bool(zd_dev.pluginProps.get("hideDimmerBroadcast", False)):
                            pass
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged color update of R={red}%, G={green}%, B={blue}%")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_color_mode(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "color_mode" in json_payload:
                valid = False
                try:
                    color_mode = json_payload["color_mode"]
                    if color_mode == "xy":
                        derived_color_mode = "color_rgb"
                        valid = True
                    elif color_mode == "color_temp":
                        derived_color_mode = "color_temp"
                        valid = True
                except (KeyError, TypeError, ValueError):
                    self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Invalid color_mode value (expected 'xy' or 'color_temp'). Event ignored.")
                if valid:
                    self.key_value_lists[zd_dev.id].append({"key": "colorMode", "value": derived_color_mode})  # noqa: reference before assignment

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_color_temp(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "color_mode" in json_payload and json_payload["color_mode"] == "color_temp" and "color_temp" in json_payload and "brightness" in json_payload:
                valid = False
                try:
                    brightness = int(json_payload["brightness"])
                    color_temp_mired = int(json_payload["color_temp"])
                    white_temperature = int(1000000 / color_temp_mired)  # noqa: reference before assignment
                    white_temperature_ui = f"{white_temperature}°K"  # noqa: reference before assignment
                    valid = True
                except ValueError:
                    self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Invalid color temperature values (expected numeric brightness/color_temp). Event ignored.")
                if valid:
                    if zd_dev.states["whiteTemperature"] != white_temperature:  # noqa: reference before assignment
                        self.key_value_lists[zd_dev.id].append({"key": "whiteTemperature", "value": white_temperature, "uiValue": white_temperature_ui})  # noqa: reference before assignment
                        if not bool(zd_dev.pluginProps.get("hideDimmerBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" white temperature update of {white_temperature_ui}")
                            # self.zigbeeLogger.info(f"previous \"{zd_dev.name}\" white temperature value was {int(zd_dev.states['whiteTemperature'])}°K")
                    else:
                        if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged white temperature update of {white_temperature_ui}")  # noqa: reference before assignment

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_position(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
        try:
            if not zd_dev.enabled:
                return
            if "position" in json_payload:
                valid = False
                try:
                    position = int(json_payload["position"])
                    valid = True
                except ValueError:
                    self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Invalid position value '{json_payload['position']}' (expected integer 0-100). Event ignored.")
                if valid:
                    if "brightnessLevel" in zd_dev.states:
                        if zd_dev.states["brightnessLevel"] != position:  # noqa: reference before assignment
                            if position > 0:
                                position_ui = "open"
                                zd_dev.updateStateImageOnServer(indigo.kStateImageSel.DimmerOn)
                            else:
                                position_ui = "close"
                                zd_dev.updateStateImageOnServer(indigo.kStateImageSel.DimmerOff)
                            self.key_value_lists[zd_dev.id].append({'key': 'brightnessLevel', 'value': position, 'uiValue': position_ui})  # noqa: reference before assignment
                            if not bool(zd_dev.pluginProps.get("hidePositionBroadcast", False)):
                                if position == 0:
                                    position_ui = "to closed"
                                elif position == 100:
                                    position_ui = "fully open"
                                elif position > zd_dev.brightness:
                                    position_ui = f"opening to position {position}%"
                                else:
                                    position_ui = f"closing to position {position}%"
                                self.zigbeeLogger.info(f"received position \"{zd_dev.name}\" {position_ui}")
                        else:
                            if not bool(zd_dev.pluginProps.get("hidePositionBroadcast", False)):
                                if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged position {position}%")  # noqa: reference before assignment
                    else:
                        self.zigbeeLogger.error(f"Device '{zd_dev.name}': State 'brightnessLevel' not found. Device may need reconfiguration.")  # noqa: reference before assignment

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
