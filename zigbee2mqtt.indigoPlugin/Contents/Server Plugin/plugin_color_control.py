#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Color control methods extracted from plugin.py

from constants import (
    DEBUG,
    ROUNDED_KELVINS,
)


class ColorControlMixin:
    """Mixin class containing color and white level control methods."""

    def action_control_device_set_color_levels(self, action, dev, zigbee_coordinator_ieee, friendly_name, topic):
        try:
            if self.globals[DEBUG]: self.logger.warning(f"processSetColorLevels ACTION:\n{action} ")

            if "redLevel" in action.actionValue and "greenLevel" in action.actionValue and  "blueLevel" in action.actionValue:
                # RGB colour being changed
                self.action_control_device_set_color_levels_rgb(action, dev, zigbee_coordinator_ieee, friendly_name, topic)
            if "whiteLevel" in action.actionValue:
                white_level = int(float(action.actionValue["whiteLevel"]))
                self.action_control_device_set_color_levels_white_level(white_level, dev, zigbee_coordinator_ieee, friendly_name, topic)
            if "whiteTemperature" in action.actionValue:
                white_temperature = int(float(action.actionValue["whiteTemperature"]))
                self.action_control_device_set_color_levels_white_temperature(white_temperature, dev, zigbee_coordinator_ieee, friendly_name, topic)
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def action_control_device_set_color_levels_rgb(self, action, dev, zigbee_coordinator_ieee, friendly_name, topic):
        try:
            props = dev.pluginProps
            if ("SupportsRGB" in props) and props["SupportsRGB"]:  # Check device supports color
                red_level = float(dev.states["redLevel"])
                green_level = float(dev.states["greenLevel"])
                blue_level = float(dev.states["blueLevel"])

                if "redLevel" in action.actionValue:
                    red_level = float(action.actionValue["redLevel"])
                if "greenLevel" in action.actionValue:
                    green_level = float(action.actionValue["greenLevel"])
                if "blueLevel" in action.actionValue:
                    blue_level = float(action.actionValue["blueLevel"])

                red = int((red_level * 256.0) / 100.0)
                red = 255 if red > 255 else red
                green = int((green_level * 256.0) / 100.0)
                green = 255 if green > 255 else green
                blue = int((blue_level * 256.0) / 100.0)
                blue = 255 if blue > 255 else blue

                topic_payload = f'{{"color":{{"r":{red},"g":{green},"b":{blue}}}}}'
                self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)

                self.logger.info(f"sent \"{dev.name}\" RGB Levels: Red {int(red_level)}%, Green {int(green_level)}%, Blue {int(blue_level)}%")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def action_control_device_set_color_levels_white_level(self, white_level, dev, zigbee_coordinator_ieee, friendly_name, topic):
        try:
            if dev.states["colorMode"] != "color_temp":
                # To force the Zigbee device into White Temperature [Color Temperature] mode, publish the devices current White Temperature
                white_temperature = dev.whiteTemperature
                kelvin = min(ROUNDED_KELVINS, key=lambda x: abs(x - white_temperature))
                mired = int(1000000 / kelvin)
                topic_payload = f'{{"color_temp": {mired}}}'

                self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)

            action_ui = "set"
            if white_level > 0:
                if white_level > dev.whiteLevel:
                    action_ui = "brighten"
                else:
                    action_ui = "dim"
            white_level_ui = f"{white_level}%"
            white_level_255 = int((white_level * 255) / 100)
            topic_payload = f'{{"brightness": {white_level_255}}}'
            self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
            self.logger.info(f"sending \"{action_ui} to {white_level_ui}\" to \"{dev.name}\"")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def action_control_device_set_color_levels_white_temperature(self, white_temperature, dev, zigbee_coordinator_ieee, friendly_name, topic):
        try:
            kelvin = min(ROUNDED_KELVINS, key=lambda x: abs(x - white_temperature))
            mired = int(1000000 / kelvin)
            # rgb, kelvin_description = ROUNDED_KELVINS[kelvin]
            topic_payload = f'{{"color_temp": {mired}}}'

            self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)

            self.logger.info(f"sent \"{dev.name}\" set White Temperature to \"{white_temperature}K\"")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
