#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023
#


# noinspection PyUnresolvedReferences
# ============================== Requirements Check ===========================

# import requirements

# ============================== Native Imports ===============================
import base64

try:
    from cryptography.fernet import Fernet  # noqa
    from cryptography.hazmat.primitives import hashes  # noqa
    from cryptography.hazmat.primitives import hashes  # noqa
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # noqa
except ImportError:
    pass

from datetime import datetime
import json
import os
import platform
import queue
import re
import socket
import sys
import threading
import traceback


# ============================== Custom Imports ===============================
try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import *
from coordinatorHandler import ThreadCoordinatorHandler
import requirements
from zigbeeHandler import ThreadZigbeeHandler

# ================================== Header ===================================
__author__    = "Autolog"
__copyright__ = ""
__license__   = "MIT"
__build__     = "unused"
__title__     = "Zigbee2mqtt Bridge Plugin for Indigo"
__version__   = "unused"

# https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password/66728699#66728699


def encode(unencrypted_password):
    # print(f"Python 3 Encode, Argument: Unencrypted Password = {unencrypted_password}")

    internal_password = MQTT_ENCRYPTION_PASSWORD_PYTHON_3  # Byte string
    # print(f"Python 3 Encode - Internal Password: {internal_password}")

    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    key = base64.urlsafe_b64encode(kdf.derive(internal_password))
    # print(f"Python 3 Encode - Key: {key}")

    f = Fernet(key)

    unencrypted_password = unencrypted_password.encode()  # str -> b
    encrypted_password = f.encrypt(unencrypted_password)
    # print(f"Python 3 Encode - Encrypted Password: {encrypted_password}")

    return key, encrypted_password


def decode(key, encrypted_password):
    # print(f"Python 3 Decode, Arguments: Key='{key}', Encrypted Password='{encrypted_password}'")

    f = Fernet(key)
    unencrypted_password = f.decrypt(encrypted_password)

    # print(f"Python 3 Decode: Unencrypted Password = {unencrypted_password}")
    
    return unencrypted_password


# noinspection PyPep8Naming
class Plugin(indigo.PluginBase):

    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs):
        super(Plugin, self).__init__(plugin_id, plugin_display_name, plugin_version, plugin_prefs)

        # logging.addLevelName(LOG_LEVEL_TOPIC, "topic")

        # def topic(self, message, *args, **kws):  # noqa [Shadowing names from outer scope = self]
        #     # if self.isEnabledFor(LOG_LEVEL_TOPIC):
        #     # Yes, logger takes its '*args' as 'args'.
        #     self.log(LOG_LEVEL_TOPIC, message, *args, **kws)
        #
        # logging.Logger.topic = topic

        self.do_not_start_stop_devices = False

        # Initialise dictionary to store plugin Globals
        self.globals = dict()

        # MASTER DEBUG FLAG FOR DEVELOPMENT ONLY
        self.globals[DEBUG] = False

        self.globals[LOCK_ZC] = threading.Lock()  # Used to lock updating of self.globals[ZC]
        self.globals[LOCK_ZD_LINKED_INDIGO_DEVICES] = threading.Lock()  # Used to lock updating of 'self.globals[ZD][zigbee_coordinator_ieee]
        self.globals[QUEUES] = dict()
        self.globals[QUEUES][MQTT_ZIGBEE2MQTT_QUEUE] = dict()

        self.globals[LOCAL_IP] = socket.gethostbyname('localhost')

        # Initialise Indigo plugin info
        self.globals[PLUGIN_INFO] = {}
        self.globals[PLUGIN_INFO][PLUGIN_ID] = plugin_id
        self.globals[PLUGIN_INFO][PLUGIN_DISPLAY_NAME] = plugin_display_name
        self.globals[PLUGIN_INFO][PLUGIN_VERSION] = plugin_version
        self.globals[PLUGIN_INFO][PATH] = indigo.server.getInstallFolderPath()
        self.globals[PLUGIN_INFO][API_VERSION] = indigo.server.apiVersion
        self.globals[PLUGIN_INFO][ADDRESS] = indigo.server.address

        log_format = logging.Formatter("%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s", datefmt="%Y-%m-%d %H:%M:%S")
        self.plugin_file_handler.setFormatter(log_format)
        self.plugin_file_handler.setLevel(LOG_LEVEL_INFO)  # Logging Level for plugin log file
        self.indigo_log_handler.setLevel(LOG_LEVEL_INFO)   # Logging level for Indigo Event Log

        self.logger = logging.getLogger("Plugin.Zigbee2mqtt")

        self.globals[ZC] = dict()  # Dictionary of  Zigbee Coordinators - keyed on Indigo Device Id
        # ZC [Dict]
        #  Indigo Coordinator Id [Dict]

        self.globals[ZC_LIST] = None

        self.globals[ZD] = dict()  # Dictionary of Zigbee devices within a dictionary of Zigbee Coordinators - keyed on Zigbee Coordinator Address
        # ZC [Dict]
        #  Coordinator_Address [Dict]
        #    Zigbee Device Address [Dict]

        self.globals[ZG] = dict()  # Dictionary of Zigbee groups within a dictionary of Zigbee Coordinators - keyed on Zigbee Coordinator Address

        self.globals[ZC_TO_INDIGO_ID] = dict()

        self.globals[ZD_TO_INDIGO_ID] = dict()  # Zigbee device to primary Indigo device

        self.globals[MQTT_FILTERS] = dict()

        self.globals[MQTT_SUPPRESS_IEEE_MISSING] = False

        # Set Plugin Config Values
        self.closed_prefs_config_ui(plugin_prefs, False)

    def __del__(self):

        indigo.PluginBase.__del__(self)

    def display_plugin_information(self):
        try:
            def plugin_information_message():
                startup_message_ui = "Plugin Information:\n"
                startup_message_ui += f"{'':={'^'}80}\n"
                startup_message_ui += f"{'Plugin Name:':<30} {self.globals[PLUGIN_INFO][PLUGIN_DISPLAY_NAME]}\n"
                startup_message_ui += f"{'Plugin Version:':<30} {self.globals[PLUGIN_INFO][PLUGIN_VERSION]}\n"
                startup_message_ui += f"{'Plugin ID:':<30} {self.globals[PLUGIN_INFO][PLUGIN_ID]}\n"
                startup_message_ui += f"{'Indigo Version:':<30} {indigo.server.version}\n"
                startup_message_ui += f"{'Indigo License:':<30} {indigo.server.licenseStatus}\n"
                startup_message_ui += f"{'Indigo API Version:':<30} {indigo.server.apiVersion}\n"
                startup_message_ui += f"{'Architecture:':<30} {platform.machine()}\n"
                startup_message_ui += f"{'Python Version:':<30} {sys.version.split(' ')[0]}\n"
                startup_message_ui += f"{'Mac OS Version:':<30} {platform.mac_ver()[0]}\n"
                startup_message_ui += f"{'Plugin Process ID:':<30} {os.getpid()}\n"
                startup_message_ui += f"{'':={'^'}80}\n"
                return startup_message_ui

            self.logger.info(plugin_information_message())

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def exception_handler(self, exception_error_message, log_failing_statement):
        filename, line_number, method, statement = traceback.extract_tb(sys.exc_info()[2])[-1]
        module = filename.split('/')
        log_message = f"'{exception_error_message}' in module '{module[-1]}', method '{method}'"
        if log_failing_statement:
            log_message = log_message + f"\n   Failing statement [line {line_number}]: '{statement}'"
        else:
            log_message = log_message + f" at line {line_number}"
        self.logger.error(log_message)

    def action_control_device(self, action, dev):
        try:
            if not dev.enabled:
                return

            dev_props = dev.pluginProps
            if "zigbee_coordinator_ieee" not in dev_props or dev_props["zigbee_coordinator_ieee"][0:2] != "0x":
                self.logger.warning(f"Unable to perform '{action.description}' action for '{dev.name}' as unable to resolve Zigbee Coordinator address.")
                return
            zigbee_coordinator_ieee = dev_props["zigbee_coordinator_ieee"]
            zc_dev_id = self.globals[ZC_TO_INDIGO_ID][zigbee_coordinator_ieee]

            group_ui = ""
            if dev.deviceTypeId == "zigbeeGroupDimmer" or dev.deviceTypeId == "zigbeeGroupRelay":
                if "zigbee_group_friendly_name" not in dev_props or dev_props["zigbee_group_friendly_name"] == "" or dev_props["zigbee_group_friendly_name"][0:1] == "-":
                    self.logger.warning(f"Unable to perform '{action.description}' action for '{dev.name}' as unable to resolve Zigbee Group name.")
                    return
                friendly_name = dev_props["zigbee_group_friendly_name"]
                group_ui = "Group "
            else:
                if "primaryIndigoDevice" not in dev_props or not dev_props["primaryIndigoDevice"]:
                    # Secondary Device
                    zigbee_device_ieee = dev.address
                else:
                    # Primary Device
                    if "zigbee_device_ieee" not in dev_props or dev_props["zigbee_device_ieee"][0:2] != "0x":
                        self.logger.warning(f"Unable to perform '{action.description}' action for '{dev.name}' as unable to resolve Zigbee Device address.")
                        return
                    else:
                        zigbee_device_ieee = dev_props["zigbee_device_ieee"]
                friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME]

            # Set default topic for turn on / off / toggle
            topic = f"{self.globals[ZC][zc_dev_id][MQTT_ROOT_TOPIC]}/{friendly_name}/set"  # e.g. "zibee2mqtt/<zigbee_coordinator_ieee>/<zigbee_device_ieee>/set"

            # ##### TURN ON ######
            if action.deviceAction == indigo.kDeviceAction.TurnOn:
                action_request = False
                match dev.deviceTypeId:
                    case "outlet":
                        topic_payload = "ON"
                        action_request = True
                    case "multiOutlet":
                        topic_payload = '{"state_l1": "ON"}'
                        action_request = True
                    case "multiOutletSecondary2" | "multiOutletSecondary3" | "multiOutletSecondary4" | "multiOutletSecondary5":
                        switch_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "2", "3", "4" or "5"
                        topic_payload = f'{{"state_l{switch_number}": "ON"}}'
                        action_request = True
                    case "multiSocket":
                        topic_payload = '{"state_left": "ON"}'
                        action_request = True
                    case "multiSocketSecondary":
                        topic_payload = '{"state_right": "ON"}'
                        action_request = True
                    case "dimmer":
                        topic_payload = "ON"
                        action_request = True
                    case "blind":
                        topic_payload = '{"state": "OPEN"}'
                        action_request = True
                    case "zigbeeGroupDimmer" | "zigbeeGroupRelay":
                        topic_payload = '{"state":"ON"}'
                        action_request = True
                if action_request:
                    action_ui = "open" if dev.deviceTypeId == "blind" else "turn on"
                    self.logger.info(f"sending \"{action_ui}\" to {group_ui}\"{dev.name}\"")
                    self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)  # noqa

            # ##### TURN OFF ######
            elif action.deviceAction == indigo.kDeviceAction.TurnOff:
                action_request = False
                match dev.deviceTypeId:
                    case "outlet":
                        topic_payload = "OFF"
                        action_request = True
                    case "multiOutlet":
                        topic_payload = '{"state_l1": "OFF"}'
                        action_request = True
                    case "multiOutletSecondary2" | "multiOutletSecondary3" | "multiOutletSecondary4" | "multiOutletSecondary5":
                        switch_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "2", "3", "4" or "5"
                        topic_payload = f'{{"state_l{switch_number}": "OFF"}}'
                        action_request = True
                    case "multiSocket":
                        topic_payload = '{"state_left": "OFF"}'
                        action_request = True
                    case "multiSocketSecondary":
                        topic_payload = '{"state_right": "OFF"}'
                        action_request = True
                    case "dimmer":
                        topic_payload = "OFF"
                        action_request = True
                    case "blind":
                        topic_payload = '{"state": "CLOSE"}'
                        action_request = True
                    case "zigbeeGroupDimmer" | "zigbeeGroupRelay":
                        topic_payload = '{"state":"OFF"}'
                        action_request = True
                if action_request:
                    action_ui = "close" if dev.deviceTypeId == "blind" else "turn off"
                    self.logger.info(f"sending \"{action_ui}\" to {group_ui}\"{dev.name}\"")
                    self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)  # noqa

            # ##### TOGGLE ######
            elif action.deviceAction == indigo.kDeviceAction.Toggle:
                if dev.onState:
                    action_request = False
                    match dev.deviceTypeId:
                        case "outlet":
                            topic_payload = "OFF"
                            action_request = True
                        case "multiOutlet":
                            topic_payload = '{"state_l1": "OFF"}'
                            action_request = True
                        case "multiOutletSecondary2" | "multiOutletSecondary3" | "multiOutletSecondary4" | "multiOutletSecondary5":
                            switch_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "2", "3", "4" or "5"
                            topic_payload = f'{{"state_l{switch_number}": "OFF"}}'
                            action_request = True
                        case "multiSocket":
                            topic_payload = '{"state_left": "OFF"}'
                            action_request = True
                        case "multiSocketSecondary":
                            topic_payload = '{"state_right": "OFF"}'
                            action_request = True
                        case "dimmer":
                            topic_payload = "OFF"
                            action_request = True
                        case "blind":
                            topic_payload = '{"state": "CLOSE"}'
                            action_request = True
                        case "zigbeeGroupDimmer" | "zigbeeGroupRelay":
                            topic_payload = '{"state":"OFF"}'
                            action_request = True
                    if action_request:
                        action_ui = "toggle close" if dev.deviceTypeId == "blind" else "toggle off"
                        self.logger.info(f"sending \"{action_ui}\" to {group_ui}\"{dev.name}\"")
                        self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)  # noqa
                else:
                    action_request = False
                    match dev.deviceTypeId:
                        case "outlet":
                            topic_payload = "ON"
                            action_request = True
                        case "multiOutlet":
                            topic_payload = '{"state_l1": "ON"}'
                            action_request = True
                        case "multiOutletSecondary2" | "multiOutletSecondary3" | "multiOutletSecondary4" | "multiOutletSecondary5":
                            switch_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "2", "3", "4" or "5"
                            topic_payload = f'{{"state_l{switch_number}": "ON"}}'
                            action_request = True
                        case "multiSocket":
                            topic_payload = '{"state_left": "ON"}'
                            action_request = True
                        case "multiSocketSecondary":
                            topic_payload = '{"state_right": "ON"}'
                            action_request = True
                        case "dimmer":
                            topic_payload = "ON"
                            action_request = True
                        case "blind":
                            topic_payload = '{"state": "OPEN"}'
                            action_request = True
                        case "zigbeeGroupDimmer" | "zigbeeGroupRelay":
                            topic_payload = '{"state":"ON"}'
                            action_request = True
                    if action_request:
                        action_ui = "toggle open" if dev.deviceTypeId == "blind" else "toggle on"
                        self.logger.info(f"sending \"{action_ui}\" to {group_ui}\"{dev.name}\"")
                        self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)  # noqa

            # ##### SET BRIGHTNESS ######
            elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
                if dev.deviceTypeId == "dimmer" or dev.deviceTypeId == "zigbeeGroupDimmer":
                    new_brightness = int(action.actionValue)   # action.actionValue contains brightness value (0 - 100)
                    action_ui = "set"
                    if new_brightness > 0:
                        if new_brightness > dev.brightness:
                            action_ui = "brighten"
                        else:
                            action_ui = "dim"
                    new_brightness_ui = f"{new_brightness}%"
                    new_brightness_255 = int((new_brightness * 255) / 100)
                    topic_payload = f'{{"brightness": {new_brightness_255}}}'
                    self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)

                    self.logger.info(f"sending \"{action_ui} to {new_brightness_ui}\" to \"{dev.name}\"")
                elif dev.deviceTypeId == "blind":
                    new_brightness = int(action.actionValue)   # action.actionValue contains brightness [Position] value (0 - 100)
                    action_ui = "position"
                    if new_brightness > 0:
                        if new_brightness > dev.brightness:
                            action_ui = "open"
                        else:
                            action_ui = "close"
                    new_brightness_ui = f"{new_brightness}%"
                    topic_payload = f'{{"position": {new_brightness}}}'
                    self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)

                    self.logger.info(f"sending \"{action_ui} to {new_brightness_ui}\" to \"{dev.name}\"")

            # # ##### BRIGHTEN BY ######
            elif action.deviceAction == indigo.kDeviceAction.BrightenBy:
                # if not dev.onState:
                #     pass  # TODO: possibly turn on if currently off?
                if dev.deviceTypeId == "dimmer" or dev.deviceTypeId == "zigbeeGroupDimmer":
                    if dev.brightness < 100:
                        brighten_by = int(action.actionValue)  # action.actionValue contains brightness increase value
                        new_brightness = dev.brightness + brighten_by
                        if new_brightness > 100:
                            new_brightness = 100
                        brighten_by_ui = f"{brighten_by}%"
                        new_brightness_255 = int((new_brightness * 255) / 100)
                        new_brightness_ui = f"{new_brightness}%"

                        topic_payload = f'{{"brightness": {new_brightness_255}}}'
                        self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                        self.logger.info(f"sending brighten by {brighten_by_ui} to {new_brightness_ui}\" to \"{dev.name}\"")
                    else:
                        self.logger.info(f"Ignoring brighten request for \"{dev.name}\" as device is already at full brightness")
                elif dev.deviceTypeId == "blind":
                    if dev.brightness < 100:
                        brighten_by = int(action.actionValue)  # action.actionValue contains brightness increase value
                        new_brightness = dev.brightness + brighten_by
                        if new_brightness > 100:
                            new_brightness = 100
                        brighten_by_ui = f"{brighten_by}%"
                        new_brightness_ui = f"{new_brightness}%"

                        topic_payload = f'{{"position": {new_brightness_ui}}}'
                        self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                        self.logger.info(f"sending open by {brighten_by_ui} to {new_brightness_ui}\" to \"{dev.name}\"")
                    else:
                        self.logger.info(f"Ignoring Position request for \"{dev.name}\" as device is already fully open")

            # ##### DIM BY ######
            elif action.deviceAction == indigo.kDeviceAction.DimBy:
                if dev.deviceTypeId == "dimmer" or dev.deviceTypeId == "zigbeeGroupDimmer":
                    if dev.onState and dev.brightness > 0:
                        dim_by = int(action.actionValue)  # action.actionValue contains brightness decrease value
                        new_brightness = dev.brightness - dim_by
                        if new_brightness < 0:
                            new_brightness_255 = 0
                            topic_payload = f'{{"brightness": {new_brightness_255}}}'
                            self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                            topic_payload = "OFF"
                            self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                            self.logger.info(f"sending \"dim to off\" to \"{dev.name}\"")
                        else:
                            dim_by_ui = f"{dim_by}%"
                            new_brightness_255 = int((new_brightness * 255) / 100)
                            new_brightness_ui = f"{new_brightness}%"

                            topic_payload = f'{{"brightness": {new_brightness_255}}}'
                            self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                            self.logger.info(f"sending \"dim by {dim_by_ui} to {new_brightness_ui}\" to \"{dev.name}\"")
                    else:
                        self.logger.info(f"Ignoring dim request for '{dev.name}'' as device is already Off")
                if dev.deviceTypeId == "blind":
                    if dev.onState and dev.brightness > 0:
                        dim_by = int(action.actionValue)  # action.actionValue contains brightness decrease value
                        new_brightness = dev.brightness - dim_by
                        if new_brightness < 0:
                            topic_payload = '{"position": 0}'
                            self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                            topic_payload = "OFF"
                            self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                            self.logger.info(f"sending fully close to \"{dev.name}\"")
                        else:
                            dim_by_ui = f"{dim_by}%"
                            new_brightness_ui = f"{new_brightness}%"

                            topic_payload = f'{{"position": {new_brightness}}}'
                            self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                            self.logger.info(f"sending close by {dim_by_ui} to {new_brightness_ui}\" to \"{dev.name}\"")
                    else:
                        self.logger.info(f"Ignoring Position request for \"{dev.name}\" as device is already fully closed")

            # ##### SET COLOR LEVELS ######
            elif action.deviceAction == indigo.kDeviceAction.SetColorLevels:
                self.action_control_device_set_color_levels(action, dev, zigbee_coordinator_ieee, friendly_name, topic)

            else:
                self.logger.warning(f"Unhandled \"actionControlDevice\" action \"{action.deviceAction}\" for \"{dev.name}\"")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

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

    def action_control_thermostat(self, action, dev):
        try:
            if not dev.enabled:
                return

            self.logger.warning(f"Action '{action.thermostatAction}' on device '{dev.name} is not supported by the plugin.")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def action_control_universal(self, action, dev):
        try:
            if not dev.enabled:
                return
            
            dev_props = dev.pluginProps
            if "zigbee_coordinator_ieee" not in dev_props or dev_props["zigbee_coordinator_ieee"][0:2] != "0x":
                self.logger.warning(f"Unable to perform '{action.description}' action for '{dev.name}' as unable to resolve Zigbee Coordinator address.")
                return
            zigbee_coordinator_ieee = dev_props["zigbee_coordinator_ieee"]

            if dev.deviceTypeId == "zigbeeGroupDimmer" or dev.deviceTypeId == "zigbeeGroupRelay":
                if "zigbee_group_friendly_name" not in dev_props or dev_props["zigbee_group_friendly_name"] == "" or dev_props["zigbee_group_friendly_name"][0:1] == "-":
                    self.logger.warning(f"Unable to perform '{action.description}' action for '{dev.name}' as unable to resolve Zigbee Group name.")
                    return
                friendly_name = dev_props["zigbee_group_friendly_name"]
            else:
                if "zigbee_device_ieee" not in dev_props or dev_props["zigbee_device_ieee"][0:2] != "0x":
                    self.logger.warning(f"Unable to perform '{action.description}' action for '{dev.name}' as unable to resolve Zigbee Device address.")
                    return
                zigbee_device_ieee = dev_props["zigbee_device_ieee"]
                friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME]

            # Set default topic for turn on / off / toggle
            zc_dev_id = self.globals[ZC_TO_INDIGO_ID][zigbee_coordinator_ieee]

            if action.deviceAction == indigo.kUniversalAction.RequestStatus:
                topic = f"{self.globals[ZC][zc_dev_id][MQTT_ROOT_TOPIC]}/{friendly_name}/get"  # e.g. "zibee2mqtt/<zigbee_coordinator_ieee>/<zigbee_device_ieee>/get"
                topic_payload = '{"state": ""}'
                self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                return

            self.logger.warning(f"Action '{action.deviceAction}' on device '{dev.name} is not supported by the plugin.")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def closed_device_config_ui(self, values_dict=None, user_cancelled=False, type_id="", dev_id=0):
        """
        Indigo method invoked after device configuration dialog is closed.

        -----
        :param values_dict:
        :param user_cancelled:
        :param type_id:
        :param dev_id:
        :return:
        """

        try:
            if user_cancelled:
                self.logger.threaddebug(f"'closedDeviceConfigUi' called with userCancelled = {str(user_cancelled)}")
                return

            if type_id == "zigbeeCoordinator":
                self.closed_device_config_ui_zigbee_coordinator(values_dict, type_id, dev_id)
            elif type_id == "zigbeeGroupDimmer" or type_id == "zigbeeGroupRelay":
                self.closed_device_config_ui_zigbee_group(values_dict, type_id, dev_id)
            else:
                self.closed_device_config_ui_zigbee_device(values_dict, type_id, dev_id)

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def closed_device_config_ui_zigbee_coordinator(self, values_dict, type_id, dev_id):
        try:
            with self.globals[LOCK_ZC]:
                if dev_id not in self.globals[ZC]:
                    self.globals[ZC][dev_id] = dict()

            self.globals[ZC][dev_id][MQTT_CLIENT_PREFIX] = values_dict.get("mqttClientPrefix", "indigo_mac")
            self.globals[ZC][dev_id][MQTT_CLIENT_ID] = f"{self.globals[ZC][dev_id][MQTT_CLIENT_PREFIX]}-D{dev_id}"
            self.globals[ZC][dev_id][MQTT_PROTOCOL] = int(values_dict.get('mqttProtocol', 4))
            self.globals[ZC][dev_id][MQTT_IP] = str(values_dict.get("mqtt_broker_ip", ""))
            self.globals[ZC][dev_id][MQTT_PORT] = int(values_dict.get("mqtt_broker_port", 0))
            self.globals[ZC][dev_id][MQTT_USERNAME] = values_dict.get("mqtt_username", "")
            self.globals[ZC][dev_id][MQTT_PASSWORD] = values_dict.get("mqtt_password", "")
            self.globals[ZC][dev_id][MQTT_ENCRYPTION_KEY] = values_dict.get("mqtt_password_encryption_key", "").encode('utf-8')
            self.globals[ZC][dev_id][MQTT_ROOT_TOPIC] = values_dict.get("zigbee2mqtt_root_topic", MQTT_ROOT_TOPIC_DEFAULT)
            if self.globals[ZC][dev_id][MQTT_ROOT_TOPIC] == "":
                self.globals[ZC][dev_id][MQTT_ROOT_TOPIC] = MQTT_ROOT_TOPIC_DEFAULT  # e.g. "zigbee2mqtt"


        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def closed_device_config_ui_zigbee_group(self, values_dict, type_id, dev_id):
        try:
            pass
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def closed_device_config_ui_zigbee_device(self, values_dict, type_id, dev_id):
        try:

            zigbee_coordinater_ieee = values_dict["zigbee_coordinator_ieee"]
            if zigbee_coordinater_ieee != "":
                zigbee_device_ieee = values_dict["zigbee_device_ieee"]
                if zigbee_device_ieee != "":
                    if zigbee_coordinater_ieee in self.globals[ZD]:
                        if zigbee_device_ieee in self.globals[ZD][zigbee_coordinater_ieee]:
                            self.globals[ZD][zigbee_coordinater_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] = dev_id

            match type_id:
                case "button":
                    pass
                case "blind":
                    pass
                case "contactSensor":
                    pass
                case "dimmer":
                    pass
                case "humidity":
                    pass
                case "illuminance":
                    pass
                case "motionSensor":
                    pass
                case "multiOutlet":
                    pass
                case "multiSensor":
                    pass
                case "multiSocket":
                    pass
                case "outlet":
                    pass
                case "presenceSensor":
                    pass
                case "radarSensor":
                    pass
                case "temperatureSensor":
                    pass
                case "thermostat":
                    pass
                case "vibrationSensor":
                    pass
                case "accelerationSensorSecondary":
                    pass
                case "humiditySensorSecondary":
                    pass
                case "illuminanceSensorSecondary":
                    pass
                case "motionSensorSecondary":
                    pass
                case "presenceSensorSecondary":
                    pass
                case "pressureSensorSecondary":
                    pass
                case "temperatureSensorSecondary":
                    pass
                case "valveSecondary":
                    pass
                case "voltageSensorSecondary":
                    pass


        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def closed_prefs_config_ui(self, values_dict=None, user_cancelled=False):
        try:
            if user_cancelled:
                return

            self.globals[DEBUG] = bool(values_dict.get("developmentDebug", False))

            # Get required Event Log and Plugin Log logging levels
            plugin_log_level = int(values_dict.get("pluginLogLevel", LOG_LEVEL_INFO))
            event_log_level = int(values_dict.get("eventLogLevel", LOG_LEVEL_INFO))

            # Ensure following logging level messages are output
            self.indigo_log_handler.setLevel(LOG_LEVEL_INFO)
            self.plugin_file_handler.setLevel(LOG_LEVEL_INFO)

            # Output required logging levels and TP Message Monitoring requirement to logs
            self.logger.info(f"Logging to Indigo Event Log at the '{LOG_LEVEL_TRANSLATION[event_log_level]}' level")
            self.logger.info(f"Logging to Plugin Event Log at the '{LOG_LEVEL_TRANSLATION[plugin_log_level]}' level")

            # Now set required logging levels
            self.indigo_log_handler.setLevel(event_log_level)
            self.plugin_file_handler.setLevel(plugin_log_level)

            self.globals[MQTT_SUPPRESS_IEEE_MISSING] = bool(values_dict.get("suppress_ieee_missing", False))

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
            return True

    def mqtt_list_zigbee_devices(self, filter="", valuesDict=None, typeId="", targetId=0):  # noqa [parameter value is not used]
        try:
            zc_dev = indigo.devices[targetId]
            zigbee_coordinator_ieee = zc_dev.address

            zigbee_devices_list = list()

            # Entry split on triple | gives: option, zigbee_coordinator_ieee, None  | All | zigbee device friendly name
            zigbee_devices_list.append((f"0|||{zigbee_coordinator_ieee}|||-- Don't Log Any Devices --", "-- Don't Log Any Devices --"))
            zigbee_devices_list.append((f"1|||{zigbee_coordinator_ieee}|||-- Log All Devices --", "-- Log All Devices --"))

            for zigbee_device_ieee, zigbee_device_details in self.globals[ZD][zigbee_coordinator_ieee].items():
                # self.logger.warning(f"zigbee_device_ieee: {zigbee_device_ieee}")
                if zigbee_device_ieee[0:2] == "0x":
                    if ZD_FRIENDLY_NAME in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                        zigbee_device_friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME]
                        zigbee_devices_list.append((f"2|||{zigbee_coordinator_ieee}|||{zigbee_device_friendly_name}", f"{zigbee_device_friendly_name}"))
                    else:
                        self.logger.warning(f"mqtt_list_zigbee_devices: Friendly name missing for zigbee device with address: {zigbee_device_ieee}")
            return sorted(zigbee_devices_list, key=lambda name: name[1].lower())  # sort by Zigbee device friendly name

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def device_start_comm(self, dev):
        try:
            if self.do_not_start_stop_devices:  # This is set on if Package requirements listed in requirements.txt are not met
                return

            self.logger.info(f"Starting '{dev.name}'")
            dev.stateListOrDisplayStateIdChanged()  # Ensure that latest devices.xml is being used

            if not dev.enabled:
                self.logger.info(f"Start cancelled as '{dev.name}' not enabled")
                return

            if dev.deviceTypeId == "zigbeeCoordinator":  # Only process if Zigbee Coordinator device
                self.device_start_comm_zigbee_coordinator(dev)
                return
            elif dev.deviceTypeId == "zigbeeGroupDimmer" or dev.deviceTypeId == "zigbeeGroupRelay":
                dev_plugin_props = dev.pluginProps
                zigbee_coordinator_ieee = dev_plugin_props.get("zigbee_coordinator_ieee", "")
                zigbee_group_friendly_name = dev_plugin_props.get("zigbee_group_friendly_name", "")
                if zigbee_group_friendly_name not in self.globals[ZG][zigbee_coordinator_ieee]:
                    self.globals[ZG][zigbee_coordinator_ieee][zigbee_group_friendly_name] = dict()
                self.globals[ZG][zigbee_coordinator_ieee][zigbee_group_friendly_name][ZG_INDIGO_DEVICE_ID] = dev.id
                return

            else:
                # Assume Zigbee device
                self.device_start_comm_zigbee_device(dev)

            # self.logger.info(f"Device '{dev.name}' Started")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def device_start_comm_zigbee_coordinator(self, zc_dev):
        try:
            # Create the thread to connect to the Zigbee Coordinator MQTT Broker
            zc_dev_id = zc_dev.id
            with self.globals[LOCK_ZC]:
                if zc_dev_id not in self.globals[ZC]:
                    self.globals[ZC][zc_dev_id] = dict()
                if zc_dev.address != "" and zc_dev.address not in self.globals[ZD]:
                    self.globals[ZD][zc_dev.address] = dict()  # Zigbee Devices
                if zc_dev.address != "" and zc_dev.address not in self.globals[ZG]:
                    self.globals[ZG][zc_dev.address] = dict()  # Zigbee Groups

            # Create Queue

            self.globals[QUEUES][MQTT_ZIGBEE2MQTT_QUEUE][zc_dev_id] = queue.Queue()  # Used to queue MQTT topics for this Zigbee Coordinator

            self.globals[ZC][zc_dev_id][MQTT_CLIENT_PREFIX] = zc_dev.pluginProps.get("mqttClientPrefix", "indigo_mac")
            self.globals[ZC][zc_dev_id][MQTT_CLIENT_ID] = f"{self.globals[ZC][zc_dev_id][MQTT_CLIENT_PREFIX]}-D{zc_dev.id}"
            self.globals[ZC][zc_dev_id][MQTT_PROTOCOL] = int(zc_dev.pluginProps.get('mqttProtocol', 4))
            self.globals[ZC][zc_dev_id][MQTT_IP] = str(zc_dev.pluginProps.get("mqtt_broker_ip", ""))
            self.globals[ZC][zc_dev_id][MQTT_PORT] = int(zc_dev.pluginProps.get("mqtt_broker_port", 0))
            self.globals[ZC][zc_dev_id][MQTT_USERNAME] = zc_dev.pluginProps.get("mqtt_username", "")
            self.globals[ZC][zc_dev_id][MQTT_PASSWORD] = zc_dev.pluginProps.get("mqtt_password", "")
            self.globals[ZC][zc_dev_id][MQTT_ENCRYPTION_KEY] = zc_dev.pluginProps.get("mqtt_password_encryption_key", "").encode('utf-8')
            self.globals[ZC][zc_dev_id][MQTT_ROOT_TOPIC] = zc_dev.pluginProps.get("zigbee2mqtt_root_topic", MQTT_ROOT_TOPIC_DEFAULT)
            if self.globals[ZC][zc_dev_id][MQTT_ROOT_TOPIC] == "":
                self.globals[ZC][zc_dev_id][MQTT_ROOT_TOPIC] = MQTT_ROOT_TOPIC_DEFAULT  # e.g. "zigbee2mqtt"

            zigbee_coordinator_ieee = zc_dev.address
            filter_entry_none = f"0|||{zigbee_coordinator_ieee}|||-- Don't Log Any Devices --"
            # filter_entry_all = f"1|||{zigbee_coordinator_ieee}|||-- Log All Devices --"
            zc_props = zc_dev.pluginProps
            mqtt_zigbee_message_filter = zc_props.get("mqtt_zigbee_device_message_filter", [filter_entry_none])

            log_message = "MQTT Topic Filtering active for the following Zigbee device(s):"  # Not used if no logging required
            filtering_required = False

            spaces = " " * 35  # used to pad log messages

            self.globals[MQTT_FILTERS][zigbee_coordinator_ieee] = list()

            if len(mqtt_zigbee_message_filter) == 0:
                self.globals[MQTT_FILTERS][zigbee_coordinator_ieee] = filter_entry_none
            else:
                for entry in mqtt_zigbee_message_filter:
                    option, zc_ieee, zd_friendly_name = entry.split("|||")
                    if option == "0":  # Ignore '-- Don't Log Any Devices --'
                        self.globals[MQTT_FILTERS][zigbee_coordinator_ieee] = ["NONE"]
                        break
                    elif option == "1":  # Ignore '-- Log All Devices --'
                        self.globals[MQTT_FILTERS][zigbee_coordinator_ieee] = ["ALL"]
                        log_message = f"{log_message}\n{spaces}All Zigbee Devices"
                        filtering_required = True
                        break
                    else:
                        self.globals[MQTT_FILTERS][zigbee_coordinator_ieee].append(f"{zd_friendly_name}")
                        spaces = " " * 24
                        log_message = f"{log_message}\n{spaces}Zigbee Device: '{zd_friendly_name}'"
                        filtering_required = True

            if filtering_required:
                self.logger.warning(f"{log_message}\n")

            self.globals[ZC][zc_dev_id][CH_EVENT] = threading.Event()
            self.globals[ZC][zc_dev_id][CH_THREAD] = ThreadCoordinatorHandler(self.globals, self.globals[ZC][zc_dev_id][CH_EVENT], zc_dev_id)
            self.globals[ZC][zc_dev_id][CH_THREAD].start()

            self.globals[ZC][zc_dev_id][ZH_EVENT] = threading.Event()
            self.globals[ZC][zc_dev_id][ZH_THREAD] = ThreadZigbeeHandler(self.globals, self.globals[ZC][zc_dev_id][ZH_EVENT], zc_dev_id)
            self.globals[ZC][zc_dev_id][ZH_THREAD].start()

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    # def didDeviceCommPropertyChange(self, origDev, newDev):
    #     # self.logger.warning(f"didDeviceCommPropertyChange: {newDev.name}")
    #
    #     # match newDev.deviceTYpeId:
    #     #     case "zigbeeCoordinator":
    #     #         return True
    #     #     case "zigbeeGroupDimmer" |
    #     if "address" in origDev.pluginProps and origDev.pluginProps['address'] != newDev.pluginProps['address']:
    #         return True
    #     return False

    def device_start_comm_zigbee_device(self, zd_dev):
        try:
            if "[UNGROUPED @" in zd_dev.name:
                self.logger.warning(f"Secondary Device '{zd_dev.name}' ungrouped from a Primary Device - please delete it!")
                return

            # Make Sure that device address is correct and also on related sub-models
            zd_dev_props = zd_dev.pluginProps
            update_address = False
            update_firmware = False
            update_device_name = False
            update_notes = False

            zigbee_coordinator_ieee = zd_dev_props.get("zigbee_coordinator_ieee", "")
            try:
                zc_dev_id = self.globals[ZC_TO_INDIGO_ID][zigbee_coordinator_ieee]
            except Exception:
                zc_dev_id = 0

            if zc_dev_id <= 0:
                self.logger.warning(f"No Zigbee Coordinator is associated with zigbee device '{zd_dev.name}'")
                return

            zigbee_device_ieee = zd_dev_props.get("zigbee_device_ieee", "")  # Only present in a primary device
            if zigbee_device_ieee != "":
                # Process primary Indigo device
                if zd_dev.address != zigbee_device_ieee:
                    self.logger.warning(f"Indigo Primary Device {zd_dev.name} address updated from '{zd_dev.address} to '{zigbee_device_ieee}")
                    zd_dev_props["address"] = zigbee_device_ieee
                    update_address = True

                software_build_id = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee].get(ZD_SOFTWARE_BUILD_ID, "")
                zd_dev_props_version = zd_dev_props.get("version", "")
                if zd_dev_props_version != software_build_id:
                    zd_dev_props["version"] = software_build_id
                    update_firmware = True

                if zd_dev_props.get("UpdateDeviceName", False):
                    indigo_derived_device_name = zd_dev_props.get("indigo_derived_device_name", "")
                    if indigo_derived_device_name != "":
                        compare_end = len(zd_dev.name) + 1
                        if zd_dev.name[0:compare_end] != indigo_derived_device_name:
                            # Check name is unique and if not, make it so
                            desired_indigo_derived_device_name = indigo_derived_device_name
                            if indigo_derived_device_name in indigo.devices:
                                name_check_count = 1
                                while True:
                                    check_name = f"{indigo_derived_device_name}_{name_check_count}"
                                    if check_name not in indigo.devices:
                                        indigo_derived_device_name = check_name
                                        break
                                    name_check_count += 1
                            update_device_name = True

                if zd_dev_props.get("UpdateNotes", False):
                    zigbee_notes = zd_dev_props.get("zigbee_description_user", "")
                    if zigbee_notes != "":
                        updated_notes = ""
                        try:
                            json_notes = json.loads(zigbee_notes)
                            json_key = zd_dev_props.get("UpdateNotesJsonList", "")
                            if json_key not in ("", "SELECT", "NONE"):
                                if json_key in json_notes:
                                    updated_notes = updated_notes + f"{json_key}: {json_notes[json_key]}\n"
                                    del json_notes[json_key]
                            for key, value in json_notes.items():
                                updated_notes = updated_notes + f"{key}: {value}\n"
                        except:
                            updated_notes = zigbee_notes
                        update_notes = True

                if update_device_name:
                    old_name = zd_dev.name
                    zd_dev.name = indigo_derived_device_name  # noqa
                    if desired_indigo_derived_device_name == indigo_derived_device_name:  # noqa
                        self.logger.info(f"Indigo Zigbee Device renamed from '{old_name}' to '{indigo_derived_device_name}'")
                    else:
                        self.logger.warning(f"Indigo Zigbee Device renamed from '{old_name}' to '{indigo_derived_device_name}' as '{desired_indigo_derived_device_name}' already in use.")

                if update_notes:
                    zd_dev.description = updated_notes  # noqa

                if update_device_name or update_notes:
                    zd_dev.replaceOnServer()

                zd_dev_props["UpdateDeviceName"] = False  # Turn off, so only actioned once
                zd_dev_props["UpdateNotes"] = False  # Turn off, so only actioned once
                if update_address | update_firmware:
                    zd_dev.replacePluginPropsOnServer(zd_dev_props)

                self.optionally_set_indigo_2021_device_sub_type(zd_dev)

                self.globals[ZD_TO_INDIGO_ID][zd_dev.address] = zd_dev.id  # Zigbee device ieee to primary Indigo device

                # zigbee_coordinator_ieee = zd_dev_props.get("zigbee_coordinator_ieee", "")  # Only present in a primary device
                # if zigbee_coordinator_ieee != "":
                #     friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME]
                #     if friendly_name != zd_dev.states["topicFriendlyName"]:
                #         zd_dev.updateStateOnServer("topicFriendlyName", friendly_name)
                #
                #

            if "zigbeePropertiesInitialised" not in zd_dev_props or not zd_dev_props["zigbeePropertiesInitialised"]:
                self.logger.warning(f"Zigbee Device {zd_dev.name} has not been initialised - Edit and Save device Settings for device.")
                return

            # Now process any existing or required secondary devices


            self.process_secondary_devices(zd_dev, zigbee_coordinator_ieee, update_device_name)

            # Check if secondary device(s) required to be created and create as necessary

            if zigbee_coordinator_ieee not in self.globals[ZD]:
                self.globals[ZD][zigbee_coordinator_ieee] = dict()  # Zigbee Coordinator
            if zigbee_device_ieee not in self.globals[ZD][zigbee_coordinator_ieee]:
                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee] = dict()  # Zigbee device

            # TODO: Consider setting image for UI depending on deviceTypeId?

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def deviceDeleted(self, dev):
        try:
            match dev.deviceTypeId:
                case "zigbeeCoordinator":
                    pass
                case "zigbeeGroupDimmer" | "zigbeeGroupRelay":
                    pass
                case _:
                    # If a primary device being deleted, zero out the link to the device in the internal store
                    primary_device = dev.pluginProps.get("primaryIndigoDevice", False)
                    if primary_device:
                        zigbee_coordinator_ieee = dev.pluginProps.get("zigbee_coordinator_ieee", "")
                        zigbee_device_ieee = dev.pluginProps.get("zigbee_device_ieee", "")
                        if ZD in self.globals:
                            if zigbee_coordinator_ieee in self.globals[ZD]:
                                if zigbee_device_ieee in self.globals[ZD][zigbee_coordinator_ieee]:
                                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] = 0

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        super(Plugin, self).deviceDeleted(dev)


    def device_stop_comm(self, dev):
        try:
            if self.do_not_start_stop_devices:  # This is set on if Package requirements listed in requirements.txt are not met
                return

            match dev.deviceTypeId:
                case "zigbeeCoordinator":
                    if CH_EVENT in self.globals[ZC][dev.id]:
                        self.globals[ZC][dev.id][CH_EVENT].set()  # Stop the MQTT Client
                    return
                case "zigbeeGroupDimmer" | "zigbeeGroupRelay":
                    return
                case _:  # Otherwise assume Zigbee device.
                    # TODO: As Zigbee device is being stopped - delete its id from internal Zigbee Devices table?
                    pass
                    # self.logger.warning(f"Stopping '{dev.name}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def device_updated(self, origDev, newDev):
        try:
            if origDev.pluginId == "com.autologplugin.indigoplugin.zigbee2mqtt":
                if origDev.deviceTypeId == "dimmer":
                    if "whiteLevel" in newDev.states:
                        if newDev.states["whiteLevel"] != newDev.states["brightnessLevel"]:
                            white_level = newDev.states["brightnessLevel"]
                            newDev.updateStateOnServer(key='whiteLevel', value=white_level)

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        super(Plugin, self).deviceUpdated(origDev, newDev)

    def menu_available_indigo_devices_filter_changed(self, values_dict, type_id, devId):
        # To force Dynamic Reload of devices
        pass
        return values_dict

    def available_indigo_devices_selected(self, values_dict, type_id, devId):
        # To force Dynamic Reload of devices

        # print(values_dict)
        pass
        return values_dict

    def get_action_config_ui_values(self, plugin_props, type_id="", dev_id=0):
        try:
            if type_id == "setWhiteLevelTemperature":
                try:
                    dimmer_device_id = int(plugin_props.get("dimmer_device_id", ""))
                except ValueError:
                    plugin_props["dimmer_device_id"] = "SELECT"

            return super(Plugin, self).getActionConfigUiValues(plugin_props, type_id, dev_id)

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def get_device_config_ui_values(self, plugin_props, type_id="", dev_id=0):
        try:
            if type_id == "zigbeeCoordinator":

                # Determine which section to initially display. If MQTT details already entered, then show the Zigbee devices
                if plugin_props["mqtt_broker_ip"] == "":
                    plugin_props["section"] = "MQTT"
                else:
                    plugin_props["section"] = "FILTER"

                # MQTT SECTION
                if "mqtt_password" not in plugin_props:
                    plugin_props["mqtt_password"] = ""

                # print(f"getPrefsConfigUiValues | mqtt_password [1]: {plugin_props[u'mqtt_password']}")

                if "mqtt_password_is_encoded" not in plugin_props:
                    plugin_props["mqtt_password_is_encoded"] = False
                if "mqtt_password" in plugin_props and plugin_props["mqtt_password_is_encoded"]:
                    plugin_props["mqtt_password_is_encoded"] = False
                    mqtt_password_encryption_key = plugin_props.get("mqtt_password_encryption_key", "")
                    plugin_props["mqtt_password"] = decode(mqtt_password_encryption_key.encode('utf-8'), plugin_props["mqtt_password"].encode('utf-8'))
                # aa = 1 + 2
                # bb = aa + 1
                # print(f"getPrefsConfigUiValues | mqtt_password [2]: {plugin_props[u'mqtt_password']}")  # TODO: DEBUG ONLY

                if "mqttClientPrefix" not in plugin_props:
                    plugin_props["mqttClientPrefix"] = ""
                if plugin_props["mqttClientPrefix"] == "":
                    try:
                        # As MQTT CLIENT PREFIX is empty, try setting it to Computer Name
                        plugin_props["mqttClientPrefix"] = socket.gethostbyaddr(socket.gethostname())[0].split(".")[0]  # Used in creation of MQTT Client Id
                    except Exception:  # noqa
                        plugin_props["mqttClientPrefix"] = "Mac"

                # COORDINATOR SECTION

                # Nothing to see here yet!

            elif  type_id == "zigbeeGroup":
                if "zigbee_group_friendly_name" not in plugin_props:
                    plugin_props["zigbee_group_friendly_name"] = "-SELECT-"  # Name of Zigbee Device - Default: "-SELECT-", "-- Select Zigbee Device(s) --"
                if "zigbee_coordinator_ieee" not in plugin_props:
                    plugin_props["zigbee_coordinator_ieee"] = "-SELECT-"  # Address of Indigo Zigbee Coordinator device - Default: "-SELECT-", "-- Select Zigbee Coordinator --"
                    plugin_props["zigbee_group_friendly_name"] = "-FIRST-"
                if plugin_props["zigbee_coordinator_ieee"] != "-SELECT-" and plugin_props["zigbee_coordinator_ieee"] != "-NONE-":
                    if plugin_props["zigbee_coordinator_ieee"] not in self.globals[ZD]:
                        plugin_props["zigbee_coordinator_ieee"] = "-NONE-"

                # if "zigbeePropertiesInitialised" not in plugin_props or not plugin_props["zigbeePropertiesInitialised"]:
                #     plugin_props["zigbeePropertyAcceleration"] = False

            elif type_id in ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES:

                # TODO: Remove below code once obsolete fields removed
                if "zigbeeCoordinatorAddress" in plugin_props:
                    del plugin_props["zigbeeCoordinatorAddress"]
                if "zigbeeDevice" in plugin_props:
                    del plugin_props["zigbeeDevice"]
                if "refreshCallbackMethod" in plugin_props:
                    if plugin_props["refreshCallbackMethod"] == "refreshUiCallback":
                        plugin_props["refreshCallbackMethod"] = "refresh_ui_callback_device"
                # TODO: See above - end of obsolete remove

                plugin_props["primaryIndigoDevice"] = True
                if "zigbee_device_ieee" not in plugin_props:
                    plugin_props["zigbee_device_ieee"] = "-SELECT-"  # Name of Zigbee Device - Default: "-SELECT-", "-- Select Zigbee Device(s) --"
                if "zigbee_coordinator_ieee" not in plugin_props:
                    plugin_props["zigbee_coordinator_ieee"] = "-SELECT-"  # Address of Indigo Zigbee Coordinator device - Default: "-SELECT-", "-- Select Zigbee Coordinator --"

                if plugin_props["zigbee_coordinator_ieee"] != "-SELECT-" and plugin_props["zigbee_coordinator_ieee"] != "-NONE-":
                    if plugin_props["zigbee_coordinator_ieee"] not in self.globals[ZD]:
                        plugin_props["zigbee_coordinator_ieee"] = "-NONE-"

                if "zigbeePropertiesInitialised" not in plugin_props or not plugin_props["zigbeePropertiesInitialised"]:
                    plugin_props["zigbeePropertyAcceleration"] = False
                    plugin_props["zigbeePropertyBattery"] = False
                    plugin_props["zigbeePropertyBrightness"] = False
                    plugin_props["zigbeePropertyAction"] = False
                    plugin_props["zigbeePropertyColor"] = False
                    plugin_props["zigbeePropertyColorName"] = False
                    plugin_props["zigbeePropertyColorTemperature"] = False
                    plugin_props["zigbeePropertyContact"] = False
                    plugin_props["zigbeePropertyDim"] = False
                    plugin_props["zigbeePropertyEnergy"] = False
                    plugin_props["zigbeePropertyHumidity"] = False
                    plugin_props["zigbeePropertyIlluminance"] = False
                    plugin_props["zigbeePropertyHvacMode"] = False
                    plugin_props["zigbeePropertyLinkQuality"] = False
                    plugin_props["zigbeePropertyOccupancy"] = False
                    plugin_props["zigbeePropertyOnOff"] = False
                    plugin_props["zigbeePropertyPosition"] = False
                    plugin_props["zigbeePropertyPower"] = False
                    plugin_props["zigbeePropertyPower_left"] = False
                    plugin_props["zigbeePropertyPower_right"] = False
                    plugin_props["zigbeePropertyPresence"] = False
                    plugin_props["zigbeePropertyPressure"] = False
                    plugin_props["zigbeePropertyRadar"] = False
                    plugin_props["zigbeePropertySetpoint"] = False
                    plugin_props["zigbeePropertyHvacState"] = False
                    plugin_props["zigbeePropertyState"] = False
                    plugin_props["zigbeePropertyStateL1"] = False
                    plugin_props["zigbeePropertyStateL2"] = False
                    plugin_props["zigbeePropertyStateL3"] = False
                    plugin_props["zigbeePropertyStateL4"] = False
                    plugin_props["zigbeePropertyStateL5"] = False
                    plugin_props["zigbeePropertyStateLeft"] = False
                    plugin_props["zigbeePropertyStateRight"] = False
                    plugin_props["zigbeePropertyTamper"] = False
                    plugin_props["zigbeePropertyTemperature"] = False
                    plugin_props["zigbeePropertyValve"] = False
                    plugin_props["zigbeePropertyVibration"] = False
                    plugin_props["zigbeePropertyVoltage"] = False

                    plugin_props["uspAcceleration"] = False
                    plugin_props["uspBattery"] = False
                    plugin_props["uspBrightness"] = False
                    plugin_props["uspAction"] = False
                    plugin_props["uspColorRGB"] = False
                    plugin_props["uspContact"] = False
                    plugin_props["uspDimmer"] = False
                    plugin_props["uspEnergy"] = False
                    plugin_props["uspHumidity"] = False
                    plugin_props["uspHvacMode"] = False
                    plugin_props["uspHvacState"] = False
                    plugin_props["uspIlluminance"] = False
                    plugin_props["uspLinkQuality"] = False
                    plugin_props["uspOccupancy"] = False
                    plugin_props["uspOnOff"] = False
                    plugin_props["uspPosition"] = False
                    plugin_props["uspPower"] = False
                    plugin_props["uspPowerLeft"] = False
                    plugin_props["uspPowerRight"] = False
                    plugin_props["uspPresence"] = False
                    plugin_props["uspPressure"] = False
                    plugin_props["uspRadar"] = False
                    plugin_props["uspSetpoint"] = False
                    plugin_props["uspState"] = False
                    plugin_props["uspStateL1"] = False
                    plugin_props["uspStateL2"] = False
                    plugin_props["uspStateL3"] = False
                    plugin_props["uspStateL4"] = False
                    plugin_props["uspStateL5"] = False
                    plugin_props["uspStateLeft"] = False
                    plugin_props["uspStateRight"] = False
                    plugin_props["uspTamper"] = False
                    plugin_props["uspTemperature"] = False
                    plugin_props["uspValve"] = False
                    plugin_props["uspVibration"] = False
                    plugin_props["uspVoltage"] = False
                    plugin_props["uspColorTemperature"] = False

                if "UpdateNotesJsonList" not in plugin_props or plugin_props["UpdateNotesJsonList"] == "":
                    plugin_props["UpdateNotesJsonList"] = "SELECT"

            elif type_id in ("accelerationSensorSecondary", "humiditySensorSecondary", "illuminanceSensorSecondary", "motionSensorSecondary",
                             "multiOutletSecondary2", "multiOutletSecondary3", "multiOutletSecondary4", "multiOutletSecondary5",
                             "multiSocketSecondary",
                             "presenceSensorSecondary", "pressureSensorSecondary",
                             "temperatureSensorSecondary", "valveSecondary"):
                plugin_props['primaryIndigoDevice'] = False
                # The following code sets the property "member_of_device_group" to True if the secondary device
                #   is associated with a primary device. If not it is set to False. This property is used
                #   in Devices.xml to display a red warning box and disable device editing if set to False.
                plugin_props['member_of_device_group'] = False
                plugin_props["primaryIndigoDevice"] = False
                dev_id_list = indigo.device.getGroupList(dev_id)
                if len(dev_id_list) > 1:
                    plugin_props['member_of_device_group'] = True
                    for linked_dev_id in dev_id_list:
                        linked_dev_props = indigo.devices[linked_dev_id].ownerProps
                        primary_device = linked_dev_props.get("primaryIndigoDevice", False)
                        if primary_device:

                            # TODO: WHAT HAPPENS IF THERE IS MORE THAN ONE SECONDARY DEVICE !!!

                            plugin_props['linkedIndigoDeviceId'] = indigo.devices[linked_dev_id].id  # TODO: Odd code, why not just set to linked_dev_id ???
                            plugin_props['linkedIndigoDevice'] = indigo.devices[linked_dev_id].name

            return super(Plugin, self).get_device_config_ui_values(plugin_props, type_id, dev_id)

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def get_device_state_list(self, dev):
        try:
            state_list = indigo.PluginBase.getDeviceStateList(self, dev)

            dev_plugin_props = dev.pluginProps

            # topic | friendly_name used on every device [Used on Coordinator and every primary Indigo Zigbee device]
            if ("primaryIndigoDevice" in dev_plugin_props and dev_plugin_props["primaryIndigoDevice"]) or dev.deviceTypeId == "zigbeeCoordinator":
                topic_friendly_name = self.getDeviceStateDictForStringType("topicFriendlyName", "Topic Friendly Name Changed", "Topic Friendly Name")
                if topic_friendly_name not in state_list:
                    state_list.append(topic_friendly_name)

            # Last Seen [Used on every primary Indigo Zigbee device]
            if "primaryIndigoDevice" in dev_plugin_props and dev_plugin_props["primaryIndigoDevice"]:
                last_seen_state = self.getDeviceStateDictForStringType("last_seen", "Last Seen Changed", "Last Seen")
                if last_seen_state not in state_list:
                    state_list.append(last_seen_state)

                # TODO: Remove - SQL Logger Test
                # id_state = self.getDeviceStateDictForStringType("id", "Id Changed", "Id")
                # if id_state not in state_list:
                #     state_list.append(id_state)


            # Acceleration State
            if (bool(dev_plugin_props.get("uspAcceleration", False)) and
                    dev_plugin_props.get("uspAccelerationIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                acceleration_state = self.getDeviceStateDictForBoolTrueFalseType("acceleration", "Acceleration Changed", "Acceleration")
                if acceleration_state not in state_list:
                    state_list.append(acceleration_state)

            # Action State(s)
            if bool(dev_plugin_props.get("uspAction", False)):
                number_of_buttons = int(dev_plugin_props.get("uspNumberOfButtons", 1))
                for button_number in range(1, (number_of_buttons + 1)):
                    button_state_id = f"button_{button_number}"
                    button_trigger_label = f"Button {button_number} Changed"
                    button_control_page_label = f"Button {button_number}"
                    button_state = self.getDeviceStateDictForStringType(button_state_id, button_trigger_label, button_control_page_label)
                    if button_state not in state_list:
                        state_list.append(button_state)
                button_state_id = "lastButtonPressed"
                button_trigger_label = "Last Button Pressed Changed"
                button_control_page_label = "Last Button Pressed"
                button_state = self.getDeviceStateDictForStringType(button_state_id, button_trigger_label, button_control_page_label)
                if button_state not in state_list:
                    state_list.append(button_state)

                on_off_state = self.getDeviceStateDictForNumberType("onOffState", "Action Changed", "Action")
                if on_off_state not in state_list:
                    state_list.append(on_off_state)

            # humidity State
            if (bool(dev_plugin_props.get("uspHumidity", False)) and
                    dev_plugin_props.get("uspHumidityIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                humidity_state = self.getDeviceStateDictForNumberType("humidity", "Humidity Changed", "Humidity")
                if humidity_state not in state_list:
                    state_list.append(humidity_state)

            # Illuminance State
            if (bool(dev_plugin_props.get("uspIlluminance", False)) and
                    dev_plugin_props.get("uspIlluminanceIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                illuminance_state = self.getDeviceStateDictForNumberType("illuminance", "Illuminance Changed", "Illuminance")
                if illuminance_state not in state_list:
                    state_list.append(illuminance_state)

            # Pressure State
            if (bool(dev_plugin_props.get("uspPressure", False)) and
                    dev_plugin_props.get("uspPressureIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                pressure_state = self.getDeviceStateDictForNumberType("pressure", "Pressure Changed", "Pressure")
                if pressure_state not in state_list:
                    state_list.append(pressure_state)

            # Presence State
            if (bool(dev_plugin_props.get("uspPresence", False)) and
                    dev_plugin_props.get("uspPresenceIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                presence_state = self.getDeviceStateDictForBoolTrueFalseType("presence", "Presence Changed", "Presence")
                if presence_state not in state_list:
                    state_list.append(presence_state)

            # RADAR [Aqara FP1] related States
            if bool(dev_plugin_props.get("uspPresenceEvent", False)):
                presence_event_state = self.getDeviceStateDictForStringType("presenceEvent", "Presence Event Changed", "Presence Event")
                if presence_event_state not in state_list:
                    state_list.append(presence_event_state)

                presence_state = self.getDeviceStateDictForBoolTrueFalseType("presence", "Presence Changed", "Presence")
                if presence_state not in state_list:
                    state_list.append(presence_state)

            # State  [used by Blind]
            if bool(dev_plugin_props.get("uspState", False)):
                state_state = self.getDeviceStateDictForStringType("state", "State Mode Changed", "State")  # TODO: Check type is correct and whether it should be internal onOffState
                if state_state not in state_list:
                    state_list.append(state_state)

            # Temperature State
            if (bool(dev_plugin_props.get("uspTemperature", False)) and
                    dev_plugin_props.get("uspTemperatureIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                temperature_state = self.getDeviceStateDictForNumberType("temperature", "Temperature Changed", "Temperature")
                if temperature_state not in state_list:
                    state_list.append(temperature_state)

            # Voltage State
            if (bool(dev_plugin_props.get("uspVoltage", False)) and
                    dev_plugin_props.get("uspVoltageIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                voltage_state = self.getDeviceStateDictForNumberType("voltage", "Voltage Changed", "Voltage")
                if voltage_state not in state_list:
                    state_list.append(voltage_state)

            # Color RGB
            if bool(dev_plugin_props.get("uspColorRGB", False)) or bool(dev_plugin_props.get("uspColorTemperature", False)):
                color_mode_state = self.getDeviceStateDictForStringType("colorMode", "Color Mode Changed", "Color Mode")
                if color_mode_state not in state_list:
                    state_list.append(color_mode_state)
                color_name_state = self.getDeviceStateDictForStringType("colorName", "Color Name Changed", "Color Name")
                if color_name_state not in state_list:
                    state_list.append(color_name_state)

            # HVAC Mode
            if bool(dev_plugin_props.get("uspHvacMode", False)):
                hvac_mode_state = self.getDeviceStateDictForStringType("hvacMode", "HVAC Mode Changed", "HVAC Mode")
                if hvac_mode_state not in state_list:
                    state_list.append(hvac_mode_state)

            # HVAC State
            if bool(dev_plugin_props.get("uspHvacState", False)):
                hvac_state_state = self.getDeviceStateDictForStringType("hvacState", "HVAC Mode Changed", "HVAC State")
                if hvac_state_state not in state_list:
                    state_list.append(hvac_state_state)

            # Link Quality State
            if (bool(dev_plugin_props.get("uspLinkQuality", False)) and
                    dev_plugin_props.get("uspLinkQualityIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                link_quality_state = self.getDeviceStateDictForNumberType("linkQuality", "Link Quality Changed", "Link Quality")
                if link_quality_state not in state_list:
                    state_list.append(link_quality_state)

            # Occupancy State
            if (bool(dev_plugin_props.get("uspOccupancy", False)) and
                    dev_plugin_props.get("uspOccupancyIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                occupancy_state = self.getDeviceStateDictForStringType("occupancy", "occupancy Changed", "Occupancy")
                if occupancy_state not in state_list:
                    state_list.append(occupancy_state)

            # Valve State
            if (bool(dev_plugin_props.get("uspValve", False)) and
                    dev_plugin_props.get("uspValveIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                valve_state = self.getDeviceStateDictForNumberType("valve", "Valve Changed", "Valve")
                if valve_state not in state_list:
                    state_list.append(valve_state)

            # Voltage State
            if (bool(dev_plugin_props.get("uspVoltage", False)) and
                    dev_plugin_props.get("uspVoltageIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                voltage_state = self.getDeviceStateDictForNumberType("voltage", "Voltage Changed", "Voltage")
                if voltage_state not in state_list:
                    state_list.append(voltage_state)

            return state_list
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def get_prefs_config_ui_values(self):
        prefs_config_ui_values = self.pluginPrefs

        pass

        return prefs_config_ui_values

    def refresh_ui_callback_device(self, values_dict, type_id="", dev_id=None):  # noqa [parameter value is not used]
        errors_dict = indigo.Dict()
        try:
            # Now process Zigbee device

            if values_dict["zigbee_device_ieee"] == "":
                values_dict["zigbee_device_ieee"] = "-SELECT-"

            if values_dict["zigbee_coordinator_ieee"] == "":
                if len(self.globals[ZC_LIST]) == 1:
                    values_dict["zigbee_coordinator_ieee"] = self.globals[ZC_LIST][0]
                else:
                    values_dict["zigbee_coordinator_ieee"] = "-SELECT-"

            if values_dict["zigbee_coordinator_ieee"] == "-SELECT-":
                values_dict["zigbee_device_ieee"] = "-FIRST-"
            elif values_dict["zigbee_coordinator_ieee"] == "-NONE-":
                values_dict["zigbee_device_ieee"] = "-NONE-"


            if not values_dict.get("list_zigbee_device_selected", False):
                self.list_zigbee_device_selected(values_dict, type_id, dev_id)  # Force selection on initial load



            usp_primary_device_main_ui_states = list()

            match type_id:
                case "button":
                    usp_primary_device_main_ui_state = "uspActionIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "contactSensor":
                    usp_primary_device_main_ui_state = "uspContactIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "blind":
                    usp_primary_device_main_ui_state = "uspPositionIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "dimmer":
                    usp_primary_device_main_ui_state = "uspOnOffIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                    usp_primary_device_main_ui_state = "uspBrightnessIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "humiditySensor":
                    usp_primary_device_main_ui_state = "uspHumidityIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "illuminanceSensor":
                    usp_primary_device_main_ui_state = "uspIlluminanceIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "motionSensor":
                    usp_primary_device_main_ui_state = "uspOccupancyIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "multiOutlet":
                    usp_primary_device_main_ui_state = "uspStateL1Indigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "multiSensor":
                    usp_primary_device_main_ui_state = "uspOccupancyIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "multiSocket":
                    usp_primary_device_main_ui_state = "uspStateLeftIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                    values_dict["uspStateRightIndigo"] = INDIGO_SECONDARY_DEVICE
                    values_dict["uspPowerLeftIndigo"] = INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE
                    values_dict["uspPowerRightIndigo"] = INDIGO_SECONDARY_DEVICE_ADDITIONAL_STATE
                    values_dict["uspLinkQualityIndigo"] = INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE
                case "outlet":
                    usp_primary_device_main_ui_state = "uspOnOffIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "presenceSensor":
                    usp_primary_device_main_ui_state = "uspPresenceIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "radarSensor":
                    usp_primary_device_main_ui_state = "uspRadarIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "temperatureSensor":
                    usp_primary_device_main_ui_state = "uspTemperatureIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "thermostat":
                    usp_primary_device_main_ui_state = "uspTemperatureIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                    usp_primary_device_main_ui_state = "uspSetpointIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE
                case "vibrationSensor":
                    usp_primary_device_main_ui_state = "uspVibrationIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE


            if type_id == "multiSocket":
                pass
            else:
                for usp_field_id in ("uspAccelerationIndigo", "uspActionIndigo", "uspBrightnessIndigo", "uspColorIndigo", "uspColorTemperatureIndigo",
                                     "uspContactIndigo", "uspEnergyIndigo", "uspHumidityIndigo", "uspIlluminanceIndigo", "uspLinkQualityIndigo", "uspOccupancyIndigo",
                                     "uspOnOffIndigo", "uspPositionIndigo", "uspPowerIndigo", "uspPowerLeftIndigo", "uspPowerRightIndigo", "uspPresenceIndigo", "uspPresenceEventIndigo", "uspPressureIndigo",
                                     "uspRadarIndigo", "uspStateIndigo", "uspStateL2Indigo", "uspStateL3Indigo", "uspStateL4Indigo", "uspStateL5Indigo", "uspStateRightIndigo",
                                     "uspTamperIndigo", "uspTemperatureIndigo", "uspSetpointIndigo", "uspValveIndigo", "uspVibrationIndigo", "uspVoltageIndigo"):
                    if usp_field_id not in usp_primary_device_main_ui_states:
                        if usp_field_id not in values_dict or values_dict[usp_field_id] not in [INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE, INDIGO_SECONDARY_DEVICE]:
                            values_dict[usp_field_id] = INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE  # Default

            # values_dict["zigbee_vendor"] = f"Random {random.randrange(100)}, USP FIELD ID: {values_dict['uspPositionIndigo']}"  # DEBUG TEST

            zd_dev = indigo.devices[dev_id]
            if zd_dev.name[0:11] == "new device ":
                values_dict["UpdateDeviceName"] = True  # Default to update name if name is Indigo default

            values_dict["show_name_exists_warning"] = True if (values_dict["UpdateDeviceName"] and values_dict["name_exists"]) else False

            if values_dict.get("UpdateNotes", False):
                zigbee_notes = values_dict.get("zigbee_description_user", "")
                if zigbee_notes != "":
                    try:
                        json.loads(zigbee_notes)  # Test whether json
                        values_dict["show_update_notes_json"] = True

                        # for key, value in json_notes.items():
                        #     updated_notes = updated_notes + f"{key}: {value}\n"
                    except:
                        values_dict["show_update_notes_json"] = False
            else:
                values_dict["show_update_notes_json"] = False

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        return values_dict, errors_dict

    def list_notes_json_keys(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]

        try:
            zigbee_notes = values_dict.get("zigbee_description_user", "")
            json_list = list()
            json_list.append(("SELECT", "- Select JSON key -"))
            if zigbee_notes != "":
                try:
                    json_notes = json.loads(zigbee_notes)  # Test whether json

                    for key, value in json_notes.items():
                        json_list.append((key, key))
                except:
                    pass
            if len(json_list) == 1:
                json_list.append(("NONE", "- None -"))

            return sorted(json_list, key=lambda name: name[1].lower())   # sort by json key

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def selected_list_notes_json_keys(self, values_dict, type_id, dev_id):
        try:
            pass
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def refresh_ui_callback_group(self, values_dict, type_id="", devId=None):  # noqa [parameter value is not used]
        errors_dict = indigo.Dict()
        try:
            # Now process Zigbee Group

            if values_dict["zigbee_group_friendly_name"] == "":
                values_dict["zigbee_group_friendly_name"] = "-SELECT-"

            if values_dict["zigbee_coordinator_ieee"] == "":
                if len(self.globals[ZC_LIST]) == 1:
                    values_dict["zigbee_coordinator_ieee"] = self.globals[ZC_LIST][0]
                else:
                    values_dict["zigbee_coordinator_ieee"] = "-SELECT-"

            if values_dict["zigbee_coordinator_ieee"] == "-SELECT-":
                values_dict["zigbee_group_friendly_name"] = "-FIRST-"
            elif values_dict["zigbee_coordinator_ieee"] == "-NONE-":
                values_dict["zigbee_group_friendly_name"] = "-NONE-"

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        return values_dict, errors_dict

    def shutdown(self):

        self.logger.info("Zigbee2mqtt Bridge plugin shutdown invoked")

    def startup(self):
        try:
            try:
                requirements.requirements_check(self.globals[PLUGIN_INFO][PLUGIN_ID])
            except ImportError as exception_error:
                self.logger.error(f"PLUGIN STOPPED: {exception_error}")
                self.do_not_start_stop_devices = True
                self.stopPlugin()

            indigo.devices.subscribeToChanges()

            for dev in indigo.devices.iter("self"):
                if dev.deviceTypeId == "zigbeeCoordinator":  # Only process if a Zigbee Coordinator Indigo device
                    self.globals[ZC][dev.id] = dict()
                    self.globals[ZC][dev.id][MQTT_CONNECTED] = False
                    if dev.address != "":
                        self.globals[ZD][dev.address] = dict()
                        self.globals[ZC_TO_INDIGO_ID][dev.address] = dev.id
                        self.globals[ZG][dev.address] = dict()

                    if self.globals[DEBUG]: self.logger.info(f"ZIGBEE COORDINATORS: {self.globals[ZC_TO_INDIGO_ID]}")

            for dev in indigo.devices.iter("self"):
                if dev.deviceTypeId != "zigbeeCoordinator":  # Only process if NOT a Zigbee Coordinator Indigo device
                    dev_plugin_props = dev.pluginProps
                    if "primaryIndigoDevice" in dev_plugin_props and dev_plugin_props["primaryIndigoDevice"]:  # Only assume primary device if prop "primaryIndigoDevice" is present and True
                        zigbee_coordinator_ieee = dev_plugin_props.get("zigbee_coordinator_ieee", "")
                        if zigbee_coordinator_ieee != "":
                            if zigbee_coordinator_ieee not in self.globals[ZD]:
                                self.globals[ZD][zigbee_coordinator_ieee] = dict()
                            if dev.address != "":
                                if dev.address not in self.globals[ZD][zigbee_coordinator_ieee]:
                                    self.globals[ZD][zigbee_coordinator_ieee][dev.address] = dict()
                                self.globals[ZD][zigbee_coordinator_ieee][dev.address][ZD_INDIGO_DEVICE_ID] = dev.id
                                self.globals[ZD_TO_INDIGO_ID][dev.address] = dev.id  # Zigbee device to primary Indigo device

        except Exception as exception_error:
                self.exception_handler(exception_error, True)  # Log error and display failing statement

    def stop_concurrent_thread(self):
        self.logger.info("Zigbee2mqtt Bridge plugin closing down")

    def validate_action_config_ui(self, values_dict, type_id, action_id):  # noqa [parameter value is not used]
        try:
            error_dict = indigo.Dict()

            white_level = -1  # Only needed to suppress a PyCharm warning!
            white_temperature = -1  # Only needed to suppress a PyCharm warning!

            if bool(values_dict.get("setWhiteLevel", True)):
                valid = True
                try:
                    white_level = int(values_dict["whiteLevel"])
                except ValueError:
                    valid = False
                if not valid or (white_level < 0 or white_level > 100):
                    error_dict["whiteLevel"] = "White Level must be an integer between 0 and 100"
                    error_dict["showAlertText"] = "You must enter an integer between 0 and 100 for White Level"
                    return False, values_dict, error_dict

            if bool(values_dict.get("setWhiteTemperature", True)):
                valid = True
                try:
                    white_temperature = int(values_dict["whiteTemperature"])
                except ValueError:
                    valid = False
                if not valid or (white_temperature < 1700 or white_temperature > 15000):
                    error_dict["whiteTemperature"] = "White Temperature must be an integer between 1700 and 15000"
                    error_dict["showAlertText"] = "You must enter an integer between 1700 and 15000 for White Temperature"
                    return False, values_dict, error_dict

            return True, values_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def validate_device_config_ui(self, values_dict=None, type_id="", dev_id=0):
        try:
            if type_id == "zigbeeCoordinator":
                values_dict, error_dict = self.validate_device_config_ui_coordinator(values_dict, type_id, dev_id)
            elif type_id == "zigbeeGroupDimmer":
                values_dict, error_dict = self.validate_device_config_ui_group_dimmer(values_dict, type_id, dev_id)
            elif type_id == "zigbeeGroupRelay":
                values_dict, error_dict = self.validate_device_config_ui_group_relay(values_dict, type_id, dev_id)
            elif type_id not in ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES:
                # Ignore validating linked devices [Sub-Models]
                return True, values_dict
            else:
                values_dict, error_dict = self.validate_device_config_ui_device(values_dict, type_id, dev_id)

            # ============================ Process Any Errors =============================
            if len(error_dict) > 0:
                return False, values_dict, error_dict
            else:
                values_dict["list_zigbee_device_selected"] = False
                values_dict["zigbeePropertiesInitialised"] = True
                return True, values_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def validate_device_config_ui_coordinator(self, values_dict=None, type_id="", dev_id=0):
        try:
            error_dict = indigo.Dict()

            mqtt_client_prefix = values_dict.get("mqttClientPrefix", "")
            mqtt_client_prefix_is_valid = True
            if len(mqtt_client_prefix) == 0:
                mqtt_client_prefix_is_valid = False
            else:
                regex = r"^[a-zA-Z0-9_-]+"
                match = re.match(regex, mqtt_client_prefix)
                if match is None:
                    mqtt_client_prefix_is_valid = False
                else:
                    if not mqtt_client_prefix[0].isalpha():
                        mqtt_client_prefix_is_valid = False

            if not mqtt_client_prefix_is_valid:
                error_message = "MQTT Client Prefix must be made up of the characters [A-Z], [a-z], [0-9], [-] or [_] and start with an alpha."
                error_dict["mqttClientPrefix"] = error_message
                error_dict["showAlertText"] = error_message
                return values_dict, error_dict

            unencrypted_password = values_dict.get("mqtt_password", "")
            if unencrypted_password != "":
                values_dict["mqtt_password_is_encoded"] = True
                key, password = encode(unencrypted_password)
                values_dict["mqtt_password"] = password
                values_dict["mqtt_password_encryption_key"] = key
            else:
                values_dict["mqtt_password_is_encoded"] = False
                values_dict["mqtt_password_encryption_key"] = ""

            return values_dict, error_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def validate_device_config_ui_group_dimmer(self, values_dict=None, type_id="", dev_id=0):
        try:
            error_dict = indigo.Dict()

            if values_dict.get("uspColor", False):
                values_dict["SupportsColor"] = True
                values_dict["SupportsRGB"] = True
            else:
                values_dict["SupportsRGB"] = False

            if values_dict.get("uspColorTemperature", False):
                values_dict["SupportsColor"] = True
                values_dict["SupportsWhite"] = True
                values_dict["SupportsWhiteTemperature"] = True
                values_dict["SupportsTwoWhiteLevels"] = False
            else:
                values_dict["SupportsWhite"] = False
                values_dict["SupportsWhiteTemperature"] = False
                values_dict["SupportsTwoWhiteLevels"] = False

            # As "SupportsColor" is common across "uspColor" and "uspColorTemperature", it can only be turned off if neither selected
            if not values_dict.get("uspColor", False) and not values_dict.get("uspColorTemperature", False):
                values_dict["SupportsColor"] = False

            return values_dict, error_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def validate_device_config_ui_group_relay(self, values_dict=None, type_id="", dev_id=0):
        try:
            error_dict = indigo.Dict()

            return values_dict, error_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def validate_device_config_ui_device(self, values_dict=None, type_id="", dev_id=0):
        try:
            error_dict = indigo.Dict()

            if values_dict["zigbee_coordinator_ieee"] == "-SELECT-":
                error_dict['zigbee_coordinator_ieee'] = "A Zigbee Coordinator must be selected"
                return False, values_dict, error_dict

            if values_dict["zigbee_device_ieee"] == "-SELECT-":
                error_dict['zigbee_device_ieee'] = "A Zigbee device must be selected"
                return False, values_dict, error_dict
            elif values_dict["zigbee_device_ieee"] == "-NONE-":
                error_dict['zigbee_device_ieee'] = "Unable to save as no available Zigbee devices"
                return False, values_dict, error_dict
            elif values_dict["zigbee_device_ieee"] == "-FIRST-":
                error_dict['zigbee_device_ieee'] = "Unable to save as no Zigbee Coordinator selected"
                return False, values_dict, error_dict

            values_dict["address"] = values_dict["zigbee_device_ieee"]

            values_dict["SupportsBatteryLevel"] = False
            values_dict["NumHumidityInputs"] = 0
            values_dict["NumTemperatureInputs"] = 0
            values_dict["ShowCoolHeatEquipmentStateUI"] = False
            values_dict["SupportsCoolSetpoint"] = False
            values_dict["SupportsEnergyMeter"] = False
            values_dict["SupportsEnergyMeterCurPower"] = False
            values_dict["SupportsAccumEnergyTotal"] = False

            values_dict["SupportsHeatSetpoint"] = False
            values_dict["SupportsHvacFanMode"] = False
            values_dict["SupportsHvacOperationMode"] = False
            values_dict["SupportsOnState"] = False
            values_dict["SupportsSensorValue"] = False
            values_dict["SupportsStatusRequest"] = False
            values_dict["supportsTemperatureReporting"] = False
            values_dict["supportsValve"] = False

            values_dict["SupportsColor"] = False
            values_dict["SupportsRGB"] = False
            values_dict["SupportsWhite"] = False
            values_dict["SupportsWhiteTemperature"] = False
            values_dict["SupportsTwoWhiteLevels"] = False

            if values_dict.get("zigbeePropertyBattery", False):
                values_dict["SupportsBatteryLevel"] = True
            else:
                values_dict["SupportsBatteryLevel"] = False

            values_dict["address"] = values_dict["zigbee_device_ieee"]

            # TODO: Consider using $nodes to check if device address is still valid - old nodes can be left behind in MQTT?

            match type_id:
                case "button":
                    # Scene (Action) validation and option settings
                    if not values_dict.get("uspAction", False):
                        error_message = "An Indigo Scene (Button) device requires an association to the Zigbee 'action' property"
                        error_dict['uspAction'] = error_message
                        error_dict["showAlertText"] = error_message

                case "blind":
                    # Blind validation and option settings
                    if not values_dict.get("uspPosition", False):
                        error_message = "An Indigo Blind device requires an association to the Zigbee 'position' property"
                        error_dict['uspPosition'] = error_message
                        error_dict["showAlertText"] = error_message
                    # elif not values_dict.get("uspOnOff", False):
                    #     error_message = "An Indigo Dimmer device requires an association to the Zigbee 'onoff' property"
                    #     error_dict['uspOnOff'] = error_message
                    #     error_dict["showAlertText"] = error_message

                case "contactSensor":
                    # Contact Sensor validation and option settings
                    if not values_dict.get("uspContact", False):
                        error_message = "An Indigo Contact Sensor device requires an association to the Zigbee 'contact' property"
                        error_dict['uspContact'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        values_dict["allowOnStateChange"] = False

                case "dimmer":
                    # Dimmer validation and option settings
                    if not values_dict.get("uspBrightness", False):
                        error_message = "An Indigo Dimmer device requires an association to the Zigbee 'brightness' property"
                        error_dict['uspBrightness'] = error_message
                        error_dict["showAlertText"] = error_message
                    elif not values_dict.get("uspOnOff", False):
                        error_message = "An Indigo Dimmer device requires an association to the Zigbee 'state' property"
                        error_dict['uspOnOff'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        if bool(values_dict.get("uspColorRGB", False)):
                            values_dict["SupportsColor"] = True
                            values_dict["SupportsRGB"] = True
                        if bool(values_dict.get("uspColorTemperature", False)):
                            values_dict["SupportsColor"] = True
                            values_dict["SupportsWhite"] = True
                            values_dict["SupportsWhiteTemperature"] = True
                            try:
                                values_dict["WhiteTemperatureMin"] = int(values_dict.get("uspKelvinMinimum", 2500))
                            except ValueError:
                                error_message = "Kelvin Minimum must be an integer"
                                error_dict['uspKelvinMinimum'] = error_message
                                error_dict["showAlertText"] = error_message
                            try:
                                values_dict["WhiteTemperatureMax"] = int(values_dict.get("uspKelvinMaximum", 9000))
                            except ValueError:
                                error_message = "Kelvin Minimum must be an integer"
                                error_dict['uspKelvinMaximum'] = error_message
                                error_dict["showAlertText"] = error_message
                        values_dict["SupportsStatusRequest"] = True

                case "humiditySensor":
                    # Humidity Sensor validation and option settings
                    if not values_dict.get("uspHumidity", False):
                        error_message = "An Indigo Humidity Sensor device requires an association to the Zigbee 'humidity' property"
                        error_dict['uspHumidity'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsSensorValue"] = True

                case "illuminanceSensor":
                    # Illuminance Sensor validation and option settings
                    if not values_dict.get("uspIlluminance", False):
                        error_message = "An Indigo Illuminance Sensor device requires an association to the Zigbee 'illuminance' property"
                        error_dict['uspIlluminance'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsSensorValue"] = True

                case "motionSensor":
                    # Motion Sensor validation and option settings
                    if not values_dict.get("uspOccupancy", False):
                        error_message = "An Indigo Motion Sensor device requires an association to the Zigbee 'occupancy' property"
                        error_dict['uspOccupancy'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        values_dict["allowOnStateChange"] = False

                case "multiOutlet":
                    # Multi-Outlet (Socket) validation and option settings
                    if not values_dict.get("uspStateL1", False):
                        error_message = "An Indigo Multi-Outlet (Socket) device requires an association to the Zigbee 'state_l1' property"
                        error_dict['uspStateL1'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        if bool(values_dict.get("uspPower", False)):
                            values_dict["SupportsEnergyMeter"] = True
                            values_dict["SupportsEnergyMeterCurPower"] = True
                        if bool(values_dict.get("uspEnergy", False)):
                            values_dict["SupportsEnergyMeter"] = True
                            values_dict["SupportsAccumEnergyTotal"] = True
                        # if bool(values_dict.get("zigbeePropertyRefresh", False)):
                        values_dict["SupportsStatusRequest"] = True

                case "multiSensor":
                    # Multi Sensor validation and option settings
                    if not values_dict.get("uspOccupancy", False):
                        error_message = "An Indigo Multi-Sensor device requires an association to the Zigbee 'occupancy' property"
                        error_dict['uspOccupancy'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        values_dict["allowOnStateChange"] = False

                case "multiSocket":
                    # Multi-Socket validation and option settings
                    if not values_dict.get("uspStateLeft", False):
                        error_message = "An Indigo Multi-Socket device requires an association to the Zigbee 'state_left' property"
                        error_dict['uspStateLeft'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        if bool(values_dict.get("uspPowerLeft", False)):
                            values_dict["SupportsEnergyMeter"] = False
                            values_dict["SupportsEnergyMeterCurPower"] = True
                        values_dict["SupportsStatusRequest"] = True

                case "outlet":
                    # Outlet (Socket) validation and option settings
                    if not values_dict.get("uspOnOff", False):
                        error_message = "An Indigo Outlet (Socket) device requires an association to the Zigbee 'state' property"
                        error_dict['uspOnOff'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        if bool(values_dict.get("uspPower", False)):
                            values_dict["SupportsEnergyMeter"] = True
                            values_dict["SupportsEnergyMeterCurPower"] = True
                        if bool(values_dict.get("uspEnergy", False)):
                            values_dict["SupportsEnergyMeter"] = True
                            values_dict["SupportsAccumEnergyTotal"] = True
                        # if bool(values_dict.get("zigbeePropertyRefresh", False)):
                        values_dict["SupportsStatusRequest"] = True

                case "presenceSensor":
                    # Presence Sensor validation and option settings
                    if not values_dict.get("uspPresence", False):
                        error_message = "An Indigo Presence Sensor device requires an association to the Zigbee 'presence' property"
                        error_dict['uspPresence'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        values_dict["allowOnStateChange"] = False

                case "radarSensor":
                    # Radar Sensor validation and option settings
                    if not values_dict.get("uspPresence", False):
                        error_message = "An Indigo Radar Sensor device requires associations to the Zigbee 'presence'"
                        error_dict['uspPresence'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        values_dict["allowOnStateChange"] = False

                case "thermostat":
                    pass
                    # Thermostat validation and option settings
                    # if not values_dict.get("uspTemperature", False):
                    #     error_message = "An Indigo Thermostat device requires an association to the Zigbee 'temperature' property"
                    #     error_dict['uspTemperature'] = error_message
                    #     error_dict["showAlertText"] = error_message
                    # elif not values_dict.get("uspSetpoint", False):
                    #     error_message = "An Indigo Thermostat device requires an association to the Zigbee 'setpoint' property"
                    #     error_dict['uspSetpoint'] = error_message
                    #     error_dict["showAlertText"] = error_message
                    # elif not values_dict.get("uspOnOff", False):
                    #     error_message = "An Indigo Thermostat device requires an association to the Zigbee 'onoff' property"
                    #     error_dict['uspOnOff'] = error_message
                    #     error_dict["showAlertText"] = error_message
                    # else:
                    #     values_dict["SupportsHeatSetpoint"] = True
                    #     values_dict["NumTemperatureInputs"] = 1
                    #     values_dict["supportsTemperatureReporting"] = True
                    #     if values_dict.get("uspHvacMode", False):
                    #         values_dict["SupportsHvacOperationMode"] = True
                    #     if (bool(values_dict.get("uspValve", False)) and
                    #             values_dict.get("uspValveIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_SECONDARY_DEVICE):
                    #         values_dict["supportsValve"] = True
                    #     if bool(values_dict.get("zigbeePropertyRefresh", False)):
                    #         values_dict["SupportsStatusRequest"] = True

                case "temperatureSensor":
                    # Temperature Sensor validation and option settings
                    if not values_dict.get("uspTemperature", False):
                        error_message = "An Indigo Temperature Sensor device requires an association to the Zigbee 'temperature' property"
                        error_dict['uspTemperature'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["supportsTemperatureReporting"] = True
                        values_dict["NumTemperatureInputs"] = 1
                        values_dict["SupportsSensorValue"] = True

                        # TODO: Is this code needed now that humidity isn't being treated specially ???

                        if values_dict.get("uspHumidity", False):
                            uspHumidityIndigo = values_dict.get("uspHumidityIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE)
                            if uspHumidityIndigo == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE:
                                values_dict["NumHumidityInputs"] = 1

                case "vibrationSensor":
                    # Motion Sensor validation and option settings
                    if not values_dict.get("uspVibration", False):
                        error_message = "An Indigo Vibration Sensor device requires an association to the Zigbee 'vibration' property"
                        error_dict['uspVibration'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        values_dict["allowOnStateChange"] = False

            return values_dict, error_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def validate_prefs_config_ui(self, values_dict): # noqa [Method is not declared static] 
        try:
            return True, values_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    #################################
    #
    # Start of bespoke plugin methods
    #
    #################################

    def list_device_state_menu_options(self, filter="", values_dict=None, type_id="", target_id=0):   # noqa [parameter value is not used]
        try:
            # <Option value="0">Primary Device - Main UI State</Option>
            # <Option value="1">Primary Device - Additional State</Option>
            # <Option value="2">Secondary Device</Option>
            # <Option value="3">Primary Device - Additional UI State</Option>

            # if self.globals[DEBUG]: self.logger.error(f"list_device_state_menu_options. filter='{filter}', type_id='{type_id}'")

            dev = indigo.devices[target_id]

            if ((filter == "button" and type_id == "button") or
                    (filter == "contact" and type_id == "contactSensor") or
                    (filter == "blind" and type_id == "blind") or
                    (filter == "brightness" and type_id == "dimmer") or
                    (filter == "onoff" and type_id == "dimmer") or
                    (filter == "humiditySensor" and type_id == "humiditySensor") or
                    (filter == "illuminanceSensor" and type_id == "illuminanceSensor") or
                    (filter == "motionSensor" and type_id == "motionSensor") or
                    (filter == "motionSensor" and type_id == "multiSensor") or
                    (filter == "onoff" and type_id == "outlet") or
                    (filter == "presenceSensor" and type_id == "presenceSensor") or
                    (filter == "radarSensor" and type_id == "radarSensor") or
                    (filter == "stateL1" and type_id == "multiOutlet") or
                    (filter == "stateLeft" and type_id == "multiSocket") or
                    (filter == "temperatureSensor" and type_id == "temperatureSensor") or
                    (filter == "temperatureSensor" and type_id == "thermostat") or
                    (filter == "vibrationSensor" and type_id == "vibrationSensor")):
                menu_list = [("0", "Primary Device - Main UI State")]
            elif ((filter == "link-quality") or
                  (filter == "last_seen") or
                  (filter == "setpoint" and type_id == "thermostat") or
                  (filter == "onoff" and type_id == "thermostat") or
                  (filter == "onoff" and type_id == "blind") or
                  (filter == "color" and type_id == "dimmer") or
                  (filter == "colorTemperature" and type_id == "dimmer") or
                  (filter == "onoff" and type_id == "dimmer") or
                  (filter == "powerLeft")):
                menu_list = [("1", "Primary Device - Additional State")]
            elif ((filter == "stateL2-5") or
                  (filter == "stateRight")):
                menu_list = [("2", "Secondary Device")]
            elif filter == "powerRight":
                menu_list = [("3", "Secondary Device - Additional State")]
            else:
                menu_list = [("1", "Primary Device - Additional State"), ("2", "Secondary Device")]
            return menu_list

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def list_zigbee_coordinators(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            self.globals[ZC_LIST] = list()

            zigbee_coordinators_list = list()
            zigbee_coordinators_list.append(("-SELECT-", "-- Select Zigbee Coordinator --"))
            for dev in indigo.devices.iter("self"):
                if dev.deviceTypeId == "zigbeeCoordinator":
                    zigbee_coordinators_list.append((dev.address, dev.name))
                    self.globals[ZC_LIST].append(dev.address)
            if len(zigbee_coordinators_list) == 2:
                del zigbee_coordinators_list[0]
                return zigbee_coordinators_list
            elif len(zigbee_coordinators_list) > 2:
                return sorted(zigbee_coordinators_list, key=lambda name: name[1].lower())   # sort by Zigbee Coordinator name
            else:
                zigbee_coordinators_list = list()
                zigbee_coordinators_list.append(("-NONE-", "No Zigbee Coordinators available"))
                return zigbee_coordinators_list
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def list_zigbee_coordinator_selected(self, values_dict, type_id, dev_id):  # noqa [parameter value is not used]
        try:
            # do whatever you need to here
            #   type_id is the device type specified in the Devices.xml
            #   devId is the device ID - 0 if it's a new device
            self.logger.error(f"Zigbee Coordinator Selected: {values_dict['zigbee_coordinator_ieee']}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        return values_dict

    def list_action_dimmer_devices(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            # This method lists dimmer devices (individual or group) support white level | temperature

            action_devices_list = list()
            action_devices_list.append(("SELECT", "- Select  Device -"))

            for dev in indigo.devices.iter("self"):
                if dev.deviceTypeId in ("dimmer", "zigbeeGroupDimmer"):
                    dev_props = dev.pluginProps
                    if dev_props["SupportsWhite"]:
                        action_devices_list.append((dev.id, dev.name))

            if len(action_devices_list) > 1:
                return sorted(action_devices_list, key=lambda name: name[1].lower())
            else:
                zigbee_devices_list = list()
                zigbee_devices_list.append(("-SELECT-", "No devices available"))

            return action_devices_list

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def list_action_dimmer_device_selected(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            pass
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def list_zigbee_coordinator_devices(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            # This method lists the zigbee devices joined to a Coordinator
            zigbee_devices_list = list()

            dev = indigo.devices[target_id]
            if dev.deviceTypeId == "zigbeeCoordinator":
                zigbee_coordinator_ieee = dev.address
            else:
                # A zigbee device
                zigbee_coordinator_ieee = values_dict.get("zigbee_coordinator_ieee", "")

            if zigbee_coordinator_ieee not in self.globals[ZD]:
                select_message = "Zigbee Coordinator yet to initialise"
                zigbee_devices_list.append(("-SELECT-", select_message))
                return zigbee_devices_list

            zigbee_device_filter = values_dict.get("zigbee_device_filter", "AVAILABLE")

            zigbee_devices_list.append(("-SELECT-", "-- Select Zigbee Device --"))
            for zigbee_device_ieee, zigbee_device_info in self.globals[ZD][zigbee_coordinator_ieee].items():
                if ZD_INDIGO_DEVICE_ID not in zigbee_device_info:
                    continue
                # indigo_zd_id = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID]
                indigo_zd_id = zigbee_device_info[ZD_INDIGO_DEVICE_ID]  # TODO: MAKE SURE THIS IS CORRECT
                if zigbee_device_filter == "AVAILABLE" and indigo_zd_id != 0:
                    continue  # As filtering on Zigbee devices available to be allocated and this device is already allocated to an Indigo device
                elif zigbee_device_filter == "ALLOCATED" and indigo_zd_id == 0:
                    continue  # As filtering on Zigbee devices already allocated to Indigo and this device isn't yet allocated to an Indigo device
                # Assume Filter set to "ALL" - so show all zigbee devices

                # self.logger.info(f"Zigbee Device List Entry: {zigbee_device_info[ZD_FRIENDLY_NAME]} [{zigbee_device_ieee}]")
                zigbee_devices_list.append((zigbee_device_ieee, zigbee_device_info[ZD_FRIENDLY_NAME]))

            if len(zigbee_devices_list) > 1:
                return sorted(zigbee_devices_list, key=lambda name: name[1].lower())   # sort by Zigbee device name
            else:
                if zigbee_device_filter == "AVAILABLE":
                    select_message = "No available devices"
                elif zigbee_device_filter == "ALLOCATED":
                    select_message = "No allocated devices "
                else:
                    select_message = "No devices on Zigbee Coordinator"

                zigbee_devices_list = list()
                zigbee_devices_list.append(("-SELECT-", select_message))

            return zigbee_devices_list

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def getDeviceConfigUiXml(self, type_id, dev_id):
        try:
            xml = self.devicesTypeDict[type_id]["ConfigUIRawXml"]

            if type_id != "zigbeeCoordinator":
                xml_modified = xml.replace("<Field>$PROPERTY$</Field>", "")
                return xml_modified

            zigbee_coordinator_ieee = indigo.devices[dev_id].address

            if zigbee_coordinator_ieee not in self.globals[ZD]:
                xml_modified = xml.replace("<Field>$PROPERTY$</Field>", "")  # Remove $PROPERTY$ override field
                return xml_modified

            def escape(string):
                escaped_string = string.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', '&quot;')
                return escaped_string
                
            xml_unique = 0
            xml_insert = ""

            for zigbee_device_ieee, zigbee_device in self.globals[ZD][zigbee_coordinator_ieee].items():
                # device_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME].upper()
                xml_zigebee_properties = f'''
    <Field id="properties_{zigbee_device_ieee}_hidden" type="checkbox" defaultValue="false" hidden="true" visibleBindingId="section" visibleBindingValue="ZIGBEE"/>
    
'''
                xml_insert = f"{xml_insert}{xml_zigebee_properties}"
                if ZD_EXPOSES not in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                    continue
                special_properties = ["device_temperature", "illuminance_lux"]  # List of handled properties with special processing
                for zigbee_device_property in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_EXPOSES]:
                    if "features" in zigbee_device_property:
                        # endpoint = zigbee_device_property.get("endpoint", "")
                        # endpoint = f" [{endpoint}]" if endpoint != "" else "xyz"
                        for zigbee_device_features_property in zigbee_device_property["features"]:
                            if "property" in zigbee_device_features_property:
                                property_to_display = f"{zigbee_device_features_property['property']}"
                                if property_to_display not in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES and property_to_display not in special_properties:
                                    property_to_display = f"{property_to_display} [Not supported by Plugin]"
                                    font_color = "red"
                                else:
                                    font_color = "orange"
                                if "description" in zigbee_device_features_property:
                                    description = zigbee_device_features_property["description"]
                                    description = escape(description)
                                else:
                                    description = "No description available from Zigbee2mqtt."
                                xml_unique += 1
                                xml_zigebee_property = f'''
        <Field id="properties_{zigbee_device_ieee}_{zigbee_device_features_property['property']}_header_{xml_unique}" type="label" defaultValue="" fontColor="{font_color}" alignWithControl="true" alwaysUseInDialogHeightCalc="false" visibleBindingId="properties_{zigbee_device_ieee}_hidden" visibleBindingValue="true">
            <Label>{property_to_display}</Label>
        </Field>
        <Field id="property_{zigbee_device_ieee}_{zigbee_device_features_property['property']}_{xml_unique}" type="label"  defaultValue="" alignWithControl="true" alwaysUseInDialogHeightCalc="false" visibleBindingId="properties_{zigbee_device_ieee}_hidden" visibleBindingValue="true">
            <Label>{description}</Label>
        </Field>
    '''
                                xml_insert = f"{xml_insert}{xml_zigebee_property}"

                    elif "property" in zigbee_device_property:
                        property_to_display = f"{zigbee_device_property['property']}"
                        if (property_to_display not in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES) and (property_to_display not in special_properties):
                            property_to_display = f"{property_to_display} [Not supported by Plugin]"
                            font_color = "red"
                        else:
                            font_color = "orange"
                        if "description" in zigbee_device_property:
                            description = zigbee_device_property["description"]
                            description = escape(description)
                        else:
                            description = "No description available from Zigbee2mqtt."
                        xml_unique += 1
                        xml_zigebee_property = f'''
        <Field id="properties_{zigbee_device_ieee}_{zigbee_device_property['property']}_header_{xml_unique}" type="label" defaultValue="" fontColor="{font_color}" alignWithControl="true" alwaysUseInDialogHeightCalc="false" visibleBindingId="properties_{zigbee_device_ieee}_hidden" visibleBindingValue="true">
            <Label>{property_to_display}</Label>
        </Field>
        <Field id="property_{zigbee_device_ieee}_{zigbee_device_property['property']}_{xml_unique}" type="label"  defaultValue="" alignWithControl="true" alwaysUseInDialogHeightCalc="false" visibleBindingId="properties_{zigbee_device_ieee}_hidden" visibleBindingValue="true">
            <Label>{description}</Label>
        </Field>
    '''
                        xml_insert = f"{xml_insert}{xml_zigebee_property}"

            xml = self.devicesTypeDict[type_id]["ConfigUIRawXml"]
            if self.globals[DEBUG]: self.logger.error(f"XML Original:\n{xml}")

            xml_modified = xml.replace("<Field>$PROPERTY$</Field>", xml_insert)
            if self.globals[DEBUG]: self.logger.info(f"XML Insertion:\n{xml_insert}")
            if self.globals[DEBUG]: self.logger.warning(f"XML Modified:\n{xml_modified}")
            return xml_modified

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def menu_zigbee_coordinator_option_selected(self, values_dict, type_id, dev_id):
        try:
            if self.globals["DEBUG"]: self.logger.warning(f"menu_zigbee_coordinator_option_selected: {values_dict['section']}")
            if values_dict["section"] != "ZIGBEE":
                zigbee_coordinator_ieee = indigo.devices[dev_id].address
                if zigbee_coordinator_ieee in self.globals[ZD]:
                     for zigbee_device_ieee_to_hide in self.globals[ZD][zigbee_coordinator_ieee]:
                        values_dict[f"properties_{zigbee_device_ieee_to_hide}_hidden"] = False
            else:
                values_dict["zigbee_device"] = "-SELECT-"
                values_dict["zigbee_vendor"] = ""
                values_dict["zigbee_model"] = ""
                values_dict["zigbee_hw"] = ""

            return values_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def list_zigbee_coordinator_device_selected(self, values_dict, type_id, dev_id):
        try:
            #   type_id is the device type specified in the Devices.xml
            #   devId is the device ID - 0 if it's a new device

            zigbee_coordinator_ieee = indigo.devices[dev_id].address
            if zigbee_coordinator_ieee not in self.globals[ZD]:
                return values_dict

            for zigbee_device_ieee_to_hide in self.globals[ZD][zigbee_coordinator_ieee]:
                values_dict[f"properties_{zigbee_device_ieee_to_hide}_hidden"] = False

            zigbee_device_ieee = values_dict["zigbee_device"]
            zigbee_hw = ""
            zigbee_model = ""
            zigbee_vendor = ""

            if zigbee_device_ieee in self.globals[ZD][zigbee_coordinator_ieee]:
                if ZD_DEFINITION in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                    zigbee_definition: dict = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION]  # noqa
                    zigbee_hw = zigbee_definition.get(ZD_DESCRIPTION_HW, "")
                    zigbee_model = zigbee_definition.get(ZD_MODEL, "")
                    zigbee_vendor = zigbee_definition.get(ZD_VENDOR, "")

                    # if self.globals[DEBUG]:
                    self.logger.warning(f"ZD_DEFINITION: Description='{zigbee_hw}', Vendor='{zigbee_vendor}', Model='{zigbee_model}'")

            values_dict["zigbee_hw"] = zigbee_hw
            values_dict["zigbee_model"] = zigbee_model
            values_dict["zigbee_vendor"] = zigbee_vendor
            values_dict[f"properties_{zigbee_device_ieee}_hidden"] = True

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        return values_dict

    def list_zigbee_groups(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            # self.logger.warning(f"list_zigbee_groups. Type: {type(values_dict)}")
            zigbee_coordinator_ieee = values_dict.get('zigbee_coordinator_ieee', "")

            zigbee_groups_list = list()

            if zigbee_coordinator_ieee not in self.globals[ZD]:
                # TODO: Change Message if selecting within a new Zigbee device
                select_message = "No Zigbee Groups Defined"
                zigbee_groups_list.append(("-SELECT-", select_message))
                return zigbee_groups_list

            zigbee_groups_list.append(("-SELECT-", "-- Select Zigbee Group --"))
            for group_friendly_name, group_details in self.globals[ZG][zigbee_coordinator_ieee].items():
                zigbee_groups_list.append((group_friendly_name, group_friendly_name))
            if len(zigbee_groups_list) == 2:
                del zigbee_groups_list[0]
                return zigbee_groups_list
            elif len(zigbee_groups_list) > 2:
                return sorted(zigbee_groups_list, key=lambda name: name[1].lower())  # sort by Zigbee Group friendly name
            else:
                zigbee_groups_list = list()
                zigbee_groups_list.append(("-NONE-", "No Zigbee Groups available"))
                return zigbee_groups_list

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def zigbee_group_selected_from_list(self, values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            pass

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def list_zigbee_group_devices(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            zigbee_coordinator_ieee = values_dict['zigbee_coordinator_ieee']

            zigbee_group_devices_list = list()

            if values_dict["zigbee_group_friendly_name"] == "-SELECT-":
                # TODO: Change Message if selecting within a new Zigbee device
                select_message = "Select Zigbee Group first"
                zigbee_group_devices_list.append(("-SELECT-", select_message))
                return zigbee_group_devices_list

            zigbee_group_devices_list.append(("-SELECT-", "-- Select Zigbee Device --"))
            zigbee_group_friendly_name = values_dict["zigbee_group_friendly_name"]
            for zigbee_group_member in self.globals[ZG][zigbee_coordinator_ieee][zigbee_group_friendly_name][ZG_MEMBERS]:
                # self.logger.warning(f"list_zigbee_group_devices. zigbee_group_member Type: {type(zigbee_group_member)}")
                zigbee_device_ieee = zigbee_group_member["ieee_address"]  # noqa
                zigbee_device_friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME]
                zigbee_group_devices_list.append((zigbee_device_ieee, zigbee_device_friendly_name))
            if len(zigbee_group_devices_list) == 2:
                del zigbee_group_devices_list[0]
                return zigbee_group_devices_list
            elif len(zigbee_group_devices_list) > 2:
                return sorted(zigbee_group_devices_list, key=lambda name: name[1].lower())  # sort by Zigbee Group friendly name
            else:
                zigbee_group_devices_list = list()
                zigbee_group_devices_list.append(("-NONE-", "No Zigbee Group Devices available"))
                return zigbee_group_devices_list

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def zigbee_group_device_selected_from_list(self, values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:

            pass

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        return values_dict

    def list_group_actions(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            zigbee_group_devices_list = list()
            if int(values_dict.get("cloned_indigo_device_id",0)) == 0:
                zigbee_group_devices_list.append(("A","Add"))
            else:
                zigbee_group_devices_list.append(("D", "Delete"))
                zigbee_group_devices_list.append(("R", "Replace"))
            return zigbee_group_devices_list

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement




    def group_action_button(self, values_dict=None, type_id="", dev_id=0):  # noqa [parameter value is not used]
        try:
            self.logger.warning(f"group_device_clone. Type_ID: {type_id}, Dev: {indigo.devices[dev_id].name}. Values Dict:\n{values_dict}")

            zigbee_coordinator_ieee = values_dict["zigbee_coordinator_ieee"]
            zigbee_device_ieee = values_dict["zigbee_device_ieee"]

            if values_dict["group_action"] == "A":  # ADD
                zd_dev_id = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID]
                zd_dev = indigo.devices[zd_dev_id]
                if zd_dev_id != 0:
                    duplicateName = f"{values_dict['zigbee_group_friendly_name']} - {zd_dev.name}"
                    duplicate_dev = indigo.device.duplicate(zd_dev_id, duplicateName=duplicateName)
                    values_dict["cloned_indigo_device_id"] = duplicate_dev.id
                    values_dict["cloned_indigo_device_name"] = duplicate_dev.name

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        return values_dict





    def list_zigbee_devices(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            zigbee_devices_list = list()

            # A zigbee device
            zigbee_coordinator_ieee = values_dict.get("zigbee_coordinator_ieee", "")

            if zigbee_coordinator_ieee not in self.globals[ZD]:
                # TODO: Change Message if selecting within a new Zigbee device
                select_message = "Zigbee Coordinator yet to initialise"
                zigbee_devices_list.append(("-SELECT-", select_message))
                return zigbee_devices_list

            # Build a list of Indigo primary devices already allocated to Zigbee devices
            allocated_devices = dict()
            for dev in indigo.devices.iter("self"):
                if dev.id != target_id and dev.deviceTypeId in ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES:
                    dev_props = dev.ownerProps
                    zigbee_device = dev_props.get("zigbee_device_ieee", "")
                    if zigbee_device != "":
                        if zigbee_device not in allocated_devices:
                            allocated_devices[zigbee_device] = dev.id
            # self.logger.warning(f"List of allocated Devices: {allocated_devices}")

            # zigbee_dev = indigo.devices[target_id]

            zigbee_device_filter = "ALL"

            zigbee_devices_list.append(("-SELECT-", "-- Select Zigbee Device --"))
            for zigbee_device_ieee, zigbee_device_info in self.globals[ZD][zigbee_coordinator_ieee].items():
                if ZD_INDIGO_DEVICE_ID not in zigbee_device_info:
                    continue
                indigo_dev_id = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID]
                zigbee_device_filter = values_dict.get("zigbee_device_filter", "AVAILABLE")
                if zigbee_device_filter == "AVAILABLE" and indigo_dev_id != 0 and indigo_dev_id != target_id:  # Not the current device
                    continue  # As filtering on Zigbee devices available to be allocated and this device is already allocated to an Indigo device
                elif zigbee_device_filter == "ALLOCATED" and indigo_dev_id == 0:
                    continue  # As filtering on Zigbee devices already allocated to Indigo and this device isn't yet allocated to an Indigo device
                # Assume Filter set to "ALL" - so show all zigbee devices

                # self.logger.info(f"Zigbee Device List Entry: {zigbee_device_info[ZD_FRIENDLY_NAME]} [{zigbee_device_ieee}]")
                zigbee_devices_list.append((zigbee_device_ieee, zigbee_device_info[ZD_FRIENDLY_NAME]))
                # already_allocated = False

            if len(zigbee_devices_list) > 1:
                return sorted(zigbee_devices_list, key=lambda name: name[1].lower())  # sort by Zigbee device name
            else:
                if zigbee_device_filter == "AVAILABLE":
                    select_message = "No available devices"
                elif zigbee_device_filter == "ALLOCATED":
                    select_message = "No allocated devices "
                else:
                    select_message = "No devices on Zigbee Coordinator"

                zigbee_devices_list = list()
                zigbee_devices_list.append(("-SELECT-", select_message))

            return zigbee_devices_list

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def list_zigbee_device_selected(self, values_dict, type_id, dev_id):
        try:
            #   type_id is the device type specified in the Devices.xml
            #   devId is the device ID - 0 if it's a new device

            values_dict["list_zigbee_device_selected"] = True

            zigbee_coordinator_ieee = values_dict["zigbee_coordinator_ieee"]
            if zigbee_coordinator_ieee not in self.globals[ZD]:
                return values_dict

            zigbee_device_ieee = values_dict["zigbee_device_ieee"]
            if zigbee_device_ieee not in self.globals[ZD][zigbee_coordinator_ieee]:
                values_dict["zigbee_description"] = ""
                values_dict["zigbee_model"] = ""
                values_dict["zigbee_vendor"] = ""
            else:
                # zigbee_device = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]
                zigbee_description_user = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee].get(ZD_DESCRIPTION_USER, "-")
                zigbee_hw = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION].get(ZD_DESCRIPTION_HW, "-")
                zigbee_model = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_MODEL]
                zigbee_vendor = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_VENDOR]
                zigbee_friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME].replace("/", " - ")

                values_dict["zigbee_description_user"] = zigbee_description_user
                values_dict["zigbee_model"] = zigbee_model
                values_dict["zigbee_vendor"] = zigbee_vendor
                values_dict["zigbee_hw"] = zigbee_hw
                values_dict["indigo_derived_device_name"] = zigbee_friendly_name.replace("/", " - ")

                indigo_name_to_check = values_dict["indigo_derived_device_name"]
                if indigo_name_to_check in indigo.devices and indigo.devices[indigo_name_to_check].id != dev_id:
                    values_dict["name_exists"] = True

                values_dict[f"properties_{zigbee_device_ieee}_hidden"] = True

                # self.logger.warning(f"ZD_DEFINITION: FN='{zigbee_friendly_name}', HW='{zigbee_hw}', Vendor='{zigbee_vendor}', Model='{zigbee_model}', Description='{zigbee_description_user}'")

            if zigbee_device_ieee == "-SELECT-" or zigbee_device_ieee == "-NONE-":
                return

            dev = indigo.devices[dev_id]

            # loop down the list of properties for this device stored from interogating the Coordinator
            for zigbee_device_property in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_PROPERTIES]:

                match zigbee_device_property:
                    case "acceleration":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyAcceleration"] = True
                        else:
                            values_dict["zigbeePropertyAcceleration"] = False

                    case "battery":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyBattery"] = True
                        else:
                            values_dict["zigbeePropertyBattery"] = False

                    case "brightness":
                        if dev.deviceTypeId == "dimmer":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyBrightness"] = True
                            else:
                                values_dict["zigbeePropertyBrightness"] = False

                    case "action":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyAction"] = True
                        else:
                            values_dict["zigbeePropertyAction"] = False

                    case "position":
                        if dev.deviceTypeId == "blind":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyPosition"] = True
                            else:
                                values_dict["zigbeePropertyPosition"] = False

                        elif dev.deviceTypeId == "thermostat":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyValve"] = True
                            else:
                                values_dict["zigbeePropertyValve"] = False

                        elif dev.deviceTypeId == "valveSecondary":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyValve"] = True
                            else:
                                values_dict["zigbeePropertyValve"] = False

                    case "color":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyColor"] = True
                        else:
                            values_dict["zigbeePropertyColor"] = False

                    case "color_temp":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyColorTemperature"] = True
                        else:
                            values_dict["zigbeePropertyColorTemperature"] = False

                    case "contact":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyContact"] = True
                        else:
                            values_dict["zigbeePropertyContact"] = False

                    case "energy":
                        zigbee_device_property = "energy"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyEnergy"] = True
                        else:
                            values_dict["zigbeePropertyEnergy"] = False

                    case "humidity":
                        zigbee_device_property = "humidity"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyHumidity"] = True
                        else:
                            values_dict["zigbeePropertyHumidity"] = False

                    case "illuminance" | "illuminance_lux":
                        zigbee_device_property = "illuminance"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyIlluminance"] = True
                        else:
                            values_dict["zigbeePropertyIlluminance"] = False

                    case "linkquality":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyLinkQuality"] = True
                        else:
                            values_dict["zigbeePropertyLinkQuality"] = False

                    case "occupancy":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyOccupancy"] = True
                        else:
                            values_dict["zigbeePropertyOccupancy"] = False

                    case "onoff":
                        match type_id:
                            case "dimmer":
                                if dev.subType != indigo.kDimmerDeviceSubType.Blind:
                                    # ASSUME COLOR DIMMER
                                    if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                        values_dict["zigbeePropertyOnOff"] = True
                                    else:
                                        values_dict["zigbeePropertyOnOff"] = False
                            case "outlet":  # and dev.subType == indigo.kDimmerDeviceSubType.Outlet:
                                # OUTLET
                                if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                    values_dict["zigbeePropertyOnOff"] = True
                                else:
                                    values_dict["zigbeePropertyOnOff"] = False

                    case "state_l1":
                        if type_id == "multiOutlet":
                            # MULTI-OUTLET
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateL1"] = True
                            else:
                                values_dict["zigbeePropertyStateL1"] = False
                    case "state_l2":
                        if type_id == "multiOutlet":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateL2"] = True
                            else:
                                values_dict["zigbeePropertyStateL2"] = False
                    case "state_l3":
                        if type_id == "multiOutlet":

                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateL3"] = True
                            else:
                                values_dict["zigbeePropertyStateL3"] = False
                    case "state_l4":
                        if type_id == "multiOutlet":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateL4"] = True
                            else:
                                values_dict["zigbeePropertyStateL4"] = False
                    case "state_l5":
                        if type_id == "multiOutlet":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateL5"] = True
                            else:
                                values_dict["zigbeePropertyStateL5"] = False

                    case "state_left":
                        if type_id == "multiSocket":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateLeft"] = True
                            else:
                                values_dict["zigbeePropertyStateLeft"] = False

                    case "state_right":
                        if type_id == "multiSocket":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateRight"] = True
                            else:
                                values_dict["zigbeePropertyStateRight"] = False

                    case "power":
                        zigbee_device_property = "power"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPower"] = True
                        else:
                            values_dict["zigbeePropertyPower"] = False

                    case "power_left":
                        zigbee_device_property = "power_left"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPowerLeft"] = True
                        else:
                            values_dict["zigbeePropertyPowerLeft"] = False

                    case "power_right":
                        zigbee_device_property = "power_right"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPowerRight"] = True
                        else:
                            values_dict["zigbeePropertyPowerRight"] = False

                    case "presence":
                        zigbee_device_property = "presence"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPresence"] = True
                        else:
                            values_dict["zigbeePropertyPresence"] = False

                    case "presence_event":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPresenceEvent"] = True
                        else:
                            values_dict["zigbeePropertyPresenceEvent"] = False

                    case "pressure":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPressure"] = True
                        else:
                            values_dict["zigbeePropertyPressure"] = False

                    case "tamper":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyTamper"] = True
                        else:
                            values_dict["zigbeePropertyTamper"] = False

                    case "temperature" | "device_temperature":
                        zigbee_device_property = "temperature"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyTemperature"] = True
                        else:
                            values_dict["zigbeePropertyTemperature"] = False

                    case "thermostat-setpoint":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertySetpoint"] = True
                        else:
                            values_dict["zigbeePropertySetpoint"] = False

                    case "vibration":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyVibration"] = True
                            else:
                                values_dict["zigbeePropertyVibration"] = False

                    case "voltage":
                        zigbee_device_property = "voltage"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyVoltage"] = True
                        else:
                            values_dict["zigbeePropertyVoltage"] = False

                    case "mode":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyHvacMode"] = True
                        else:
                            values_dict["zigbeePropertyHvacMode"] = False

                    case "state":
                        match type_id:
                            case "thermostat" :
                                # THERMOSTAT
                                if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                    values_dict["zigbeePropertyHvacState"] = True
                                else:
                                    values_dict["zigbeePropertyHvacState"] = False
                            case "dimmer":
                                if dev.subType == indigo.kDimmerDeviceSubType.Blind:
                                    # BLIND / SHADE
                                    if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                        values_dict["zigbeePropertyState"] = True
                                    else:
                                        values_dict["zigbeePropertyState"] = False

                    case "refresh":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyRefresh"] = True
                        else:
                            values_dict["zigbeePropertyRefresh"] = False

                    case "water":
                        pass  # Property not supported

                    case "custom":
                        pass  # Property not supported

                    case ("heating-setpoint","cooling-setpoint","thermostat-setpoint","mode","fanmode,state","modes","fanmodes"):
                        pass  # Property not supported (yet?)
                        if self.globals[DEBUG]: self.logger.warning(f"Zigbee Device '{zigbee_device_ieee}': property unsupported '{zigbee_device_property}'")
                    case _:
                        pass  # Property not supported
                        if self.globals[DEBUG]: self.logger.warning(f"Zigbee Device '{zigbee_device_ieee}' has unsupported property '{zigbee_device_property}'")

            # # Consistency checking for dimmer (color / white) - only allow color and/or white if dim is true
            # if not values_dict.get("ZigbeePropertyDim", False):
            #     values_dict["zigbeePropertyColor"] = False
            #     values_dict["zigbeePropertyColorTemperature"] = False

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        return values_dict

    def list_zigbee_device_properties(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]

        try:
            zigbee_coordinator_ieee = indigo.devices[target_id].address
            if zigbee_coordinator_ieee not in self.globals[ZD]:
                return values_dict

            zigbee_device_ieee = values_dict.get("zigbee_device", "-NONE-")

            zigbee_device_properties_list = []
            if zigbee_device_ieee == "-SELECT-" or zigbee_device_ieee == "-NONE-":
                return zigbee_device_properties_list

            for zigbee_device_property in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_EXPOSES]:
                if "property" in zigbee_device_property:
                    zigbee_device_properties_list.append((zigbee_device_property['property'], zigbee_device_property['property']))

            return sorted(zigbee_device_properties_list, key=lambda name: name[1].lower())   # sort by zigbee device property name

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def zigbee_device_property_selected(self, values_dict, type_id, dev_id):
        try:
            pass
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def refresh_zigbee_device(self, values_dict=None, type_id="", target_id=0):
        try:
            values_dict_updated = self.list_zigbee_device_selected(values_dict, type_id, target_id)

            return values_dict_updated

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def optionally_set_indigo_2021_device_sub_type(self, dev):
        try:
            if dev.deviceTypeId == "contactSensor":
                if dev.subType != indigo.kSensorDeviceSubType.DoorWindow:
                    dev.subType = indigo.kSensorDeviceSubType.DoorWindow
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "dimmer":
                if dev.ownerProps.get("SupportsColor", False):
                    dev_subtype_to_test_against = indigo.kDimmerDeviceSubType.ColorDimmer
                else:
                    dev_subtype_to_test_against = indigo.kDimmerDeviceSubType.Dimmer
                if dev.subType != dev_subtype_to_test_against:
                    dev.subType = dev_subtype_to_test_against
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "humiditySensor" or dev.deviceTypeId == "humiditySensorSecondary":
                if dev.subType != indigo.kSensorDeviceSubType.Humidity:
                    dev.subType = indigo.kSensorDeviceSubType.Humidity
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "illuminanceSensor" or dev.deviceTypeId == "illumianceSensorSecondary":
                if dev.subType != indigo.kSensorDeviceSubType.Illuminance:
                    dev.subType = indigo.kSensorDeviceSubType.Illuminance
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "multiOutlet" or dev.deviceTypeId == "multiOutletSecondary2" or dev.deviceTypeId == "multiOutletSecondary3" or dev.deviceTypeId == "multiOutletSecondary4" or dev.deviceTypeId == "multiOutletSecondary5":
                if dev.subType != indigo.kRelayDeviceSubType.Outlet:
                    dev.subType = indigo.kRelayDeviceSubType.Outlet
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "multiSocket" or dev.deviceTypeId == "multiSocketSecondary":
                if dev.subType != indigo.kRelayDeviceSubType.Outlet:
                    dev.subType = indigo.kRelayDeviceSubType.Outlet
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "motionSensor" or dev.deviceTypeId == "multiSensor" or dev.deviceTypeId == "motionSensorSecondary":
                if dev.subType != indigo.kSensorDeviceSubType.Motion:
                    dev.subType = indigo.kSensorDeviceSubType.Motion
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "outlet":
                if dev.subType != indigo.kRelayDeviceSubType.Outlet:
                    dev.subType = indigo.kRelayDeviceSubType.Outlet
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "presenceSensor" or dev.deviceTypeId == "radar":
                if dev.subType != indigo.kSensorDeviceSubType.Presence:
                    dev.subType = indigo.kSensorDeviceSubType.Presence
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "temperatureSensor" or dev.deviceTypeId == "temperatureSensorSecondary":
                if dev.subType != indigo.kSensorDeviceSubType.Temperature:
                    dev.subType = indigo.kSensorDeviceSubType.Temperature
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "accelerationSensorSecondary":
                if dev.subType != indigo.kDeviceSubType.Security:
                    dev.subType = indigo.kDeviceSubType.Security
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "presenceSensorSecondary":
                if dev.subType != indigo.kSensorDeviceSubType.Presence:
                    dev.subType = indigo.kSensorDeviceSubType.Presence
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "pressureSensorSecondary":
                if dev.subType != indigo.kSensorDeviceSubType.Pressure:
                    dev.subType = indigo.kSensorDeviceSubType.Pressure
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "valveSecondary":
                if dev.subType != indigo.kDimmerDeviceSubType.Valve:
                    dev.subType = indigo.kDimmerDeviceSubType.Valve
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "vibrationSensor":
                if dev.subType != indigo.kSensorDeviceSubType.Vibration:
                    dev.subType = indigo.kSensorDeviceSubType.Vibration
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "voltageSensorSecondary":
                if dev.subType != indigo.kSensorDeviceSubType.Voltage:
                    dev.subType = indigo.kSensorDeviceSubType.Voltage
                    dev.replaceOnServer()

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def set_white_level_temperature(self, action, dev):
        try:
            if self.globals[DEBUG]: self.logger.warning(f"processSetColorLevels ACTION:\n{action} ")

            valid = False
            try:
                dev_id = int(action.props.get("dimmer_device_id","RAISE ERROR AS MISSING!"))
                if dev_id in indigo.devices:
                    valid = True
            except ValueError:
                pass

            if not valid:
                self.logger.warning(f"Unable to perform '{action.description}' action as no device selected.")
                return

            dev = indigo.devices[dev_id]
            dev_plugin_props = dev.pluginProps
            if "zigbee_coordinator_ieee" not in dev_plugin_props or dev_plugin_props["zigbee_coordinator_ieee"][0:2] != "0x":
                self.logger.warning(f"Unable to perform '{action.description}' action for '{dev.name}' as unable to resolve Zigbee Coordinator address.")
                return
            zigbee_coordinator_ieee = dev_plugin_props["zigbee_coordinator_ieee"]
            zc_dev_id = self.globals[ZC_TO_INDIGO_ID][zigbee_coordinator_ieee]

            # group_ui = ""
            if dev.deviceTypeId == "zigbeeGroupDimmer" or dev.deviceTypeId == "zigbeeGroupRelay":
                if "zigbee_group_friendly_name" not in dev_plugin_props or dev_plugin_props["zigbee_group_friendly_name"] == "" or dev_plugin_props["zigbee_group_friendly_name"][0:1] == "-":
                    self.logger.warning(f"Unable to perform '{action.description}' action for '{dev.name}' as unable to resolve Zigbee Group name.")
                    return
                friendly_name = dev_plugin_props["zigbee_group_friendly_name"]
                # group_ui = "Group "
            else:
                if "zigbee_device_ieee" not in dev_plugin_props or dev_plugin_props["zigbee_device_ieee"][0:2] != "0x":
                    self.logger.warning(f"Unable to perform '{action.description}' action for '{dev.name}' as unable to resolve Zigbee Device address.")
                    return
                zigbee_device_ieee = dev_plugin_props["zigbee_device_ieee"]
                friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME]

            # Set default topic
            topic = f"{self.globals[ZC][zc_dev_id][MQTT_ROOT_TOPIC]}/{friendly_name}/set"

            new_action = dict()
            new_action["actionValue"] = dict()
            if action.props["setWhiteLevel"]:
                white_level = int(action.props["whiteLevel"])
                self.action_control_device_set_color_levels_white_level(white_level, dev, zigbee_coordinator_ieee, friendly_name, topic)
            if action.props["setWhiteTemperature"]:
                white_temperature = int(action.props["whiteTemperature"])
                self.action_control_device_set_color_levels_white_temperature(white_temperature, dev, zigbee_coordinator_ieee, friendly_name, topic)

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_secondary_devices(self, primary_dev, zigbee_coordinator_ieee, update_device_name):
        try:
            primary_dev_id = primary_dev.id
            primary_dev_type_id = primary_dev.deviceTypeId
            # primary_dev_sub_type = getattr(primary_dev, "subType", None)

            if primary_dev_type_id not in INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE or len(INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE[primary_dev_type_id]) == 0:
                # TODO: Unsupported Indigo device type
                return

            existing_secondary_dev_id_list = indigo.device.getGroupList(primary_dev_id)
            existing_secondary_dev_id_list.remove(primary_dev_id)  # Remove Primary device from list

            # At this point we have a list of secondary devices

            existing_secondary_devices = dict()
            for existing_secondary_dev_id in existing_secondary_dev_id_list:
                existing_secondary_devices[indigo.devices[existing_secondary_dev_id].deviceTypeId] = existing_secondary_dev_id

                # existing_secondary_devices["uspStateL1Indigo"] = 123
                # existing_secondary_devices["uspStateL2Indigo"] = 456
                # existing_secondary_devices["uspStateL3Indigo"] = 789


            # At this point we have created a dictionary of sub-model types with their associated Indigo device Ids

            primary_dev_props = primary_dev.pluginProps

            for secondary_device_type_id in INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE[primary_dev_type_id]:

                # note "usp" prefix stands for "User Selectable Property" :)

                usp_indigo_name = INDIGO_SUB_TYPE_INFO[secondary_device_type_id][0]  # e.g. "uspIlluminanceIndigo"

                usp_property = usp_indigo_name[:-6]  # Remove 'Indigo' from usp e.g. "uspIlluminanceIndigo" > "uspIlluminance"

                usp_required = False
                if usp_property in primary_dev_props and primary_dev_props[usp_property]:
                    usp_required = True

                required_state_type = primary_dev_props.get(usp_indigo_name, INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE)  # default to additional state
                if not usp_required or required_state_type != INDIGO_SECONDARY_DEVICE:
                    # At this point the property is not required or
                    #   the state associated with the property is not required in a secondary device
                    #   therefore, if it exists, remove it.
                    self.process_secondary_devices_remove_existing(primary_dev, zigbee_coordinator_ieee, existing_secondary_devices, secondary_device_type_id)
                else:
                    # TODO: CHECK FOR USP = TRUE
                    if not usp_required:
                        continue  # As property not required, continue to check next USP

                    self.process_secondary_devices_create_update_new(primary_dev, zigbee_coordinator_ieee, update_device_name, existing_secondary_devices, secondary_device_type_id)



        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_secondary_devices_remove_existing(self, primary_dev, zigbee_coordinator_ieee, existing_secondary_devices, secondary_device_type_id):
        try:
            # At this point the property is not required or
            #   the state associated with the property is not required in a secondary device
            #   therefore, if it exists, remove it.
            if secondary_device_type_id in existing_secondary_devices:
                secondary_device_id = existing_secondary_devices[secondary_device_type_id]
                secondary_dev = indigo.devices[secondary_device_id]

                indigo.device.ungroupDevice(secondary_dev)
                secondary_dev.refreshFromServer()
                primary_dev.refreshFromServer()

                secondary_dev_props = secondary_dev.ownerProps
                secondary_dev_props["member_of_device_group"] = False  # Reset to False as no longer a member of a device group
                secondary_dev.replacePluginPropsOnServer(secondary_dev_props)

                ungrouped_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ungrouped_name = f"{secondary_dev.name} [UNGROUPED @ {ungrouped_time}]"
                secondary_dev.name = ungrouped_name
                secondary_dev.replaceOnServer()

                # Now remove link to secondary device from within primary device
                primary_props = primary_dev.pluginProps

                match secondary_device_type_id:

                    case "accelerationSensorSecondary":
                        primary_props["secondaryDeviceAccelerationSensor"] = 0
                    case "humiditySensorSecondary":
                        primary_props["secondaryDeviceHumiditySensor"] = 0
                    case "illuminanceSensorSecondary":
                        primary_props["secondaryDeviceIlluminanceSensor"] = 0
                    case "motionSensorSecondary":
                        primary_props["secondaryDeviceMotionSensor"] = 0
                    case "multiOutletSecondary2":
                        primary_props["secondaryDeviceMultiOutlet2"] = 0
                    case "multiOutletSecondary3":
                        primary_props["secondaryDeviceMultiOutlet3"] = 0
                    case "multiOutletSecondary4":
                        primary_props["secondaryDeviceMultiOutlet4"] = 0
                    case "multiOutletSecondary5":
                        primary_props["secondaryDeviceMultiOutlet5"] = 0
                    case "multiSocketSecondary":
                        primary_props["secondaryDeviceMultiSocket"] = 0
                    case "presenceSensorSecondary":
                        primary_props["secondaryDevicePresenceSensor"] = 0
                    case "pressureSensorSecondary":
                        primary_props["secondaryDevicePressureSensor"] = 0
                    case "temperatureSensorSecondary":
                        primary_props["secondaryDeviceTemperatureSensor"] = 0
                    case "valveSecondary":
                        primary_props["secondaryDeviceValve"] = 0
                    case "voltageSensorSecondary":
                        primary_props["secondaryDeviceVoltageSensor"] = 0

                primary_dev.replacePluginPropsOnServer(primary_props)

                self.logger.warning(f"Secondary Device '{secondary_dev.name}' ungrouped from Primary Device '{primary_dev.name}' - please delete it!")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_secondary_devices_create_update_new(self, primary_dev, zigbee_coordinator_ieee, update_device_name, existing_secondary_devices, secondary_device_type_id):
        try:
            primary_props = primary_dev.ownerProps

            if secondary_device_type_id not in existing_secondary_devices:  # TODO: WARNING: ONLY HANDLES 1 occurrence of a subtype
                                                                            # TODO:   WORKED ROUND THIS FOR MULTI-OUTLET BY HAVING DIFFERENT SECONDARY DEVICE TYPES
                # Create Secondary Device
                if hasattr(primary_dev, "subType"):  # If subType property supported for primary device - assume supported on Secondary
                    usp_indigo_name = INDIGO_SUB_TYPE_INFO[secondary_device_type_id][1][0]
                else:
                    usp_indigo_name = INDIGO_SUB_TYPE_INFO[secondary_device_type_id][1][1]

                secondary_name = f"{primary_dev.name} [{usp_indigo_name}]"  # Create default name
                # Check name is unique and if not, make it so
                if secondary_name in indigo.devices:
                    name_check_count = 1
                    while True:
                        check_name = f"{secondary_name}_{name_check_count}"
                        if check_name not in indigo.devices:
                            secondary_name = check_name
                            break
                        name_check_count += 1



                required_props_list = INDIGO_SUB_TYPE_INFO[secondary_device_type_id][2]

                props_dict = dict()
                props_dict["zigbee_coordinator_ieee"] = zigbee_coordinator_ieee
                props_dict["zigbeePropertiesInitialised"] = True
                props_dict["member_of_device_group"] = True
                props_dict["linkedPrimaryIndigoDeviceId"] = primary_dev.id
                props_dict["linkedPrimaryIndigoDevice"] = primary_dev.name
                props_dict["associatedZigbeeDevice"] = zigbee_coordinator_ieee
                props_dict["primaryIndigoDevice"] = False

                for key, value in required_props_list:
                    props_dict[key] = value

                secondary_dev = indigo.device.create(protocol=indigo.kProtocol.Plugin,
                                                     address=primary_dev.address,
                                                     description="",
                                                     name=secondary_name,
                                                     folder=primary_dev.folderId,
                                                     pluginId="com.autologplugin.indigoplugin.zigbee2mqtt",
                                                     deviceTypeId=secondary_device_type_id,
                                                     groupWithDevice=primary_dev.id,
                                                     props=props_dict)

                # Manually need to set the model and subModel names (for UI only)
                secondary_dev_id = secondary_dev.id
                secondary_dev = indigo.devices[secondary_dev_id]  # Refresh Indigo Device to ensure groupWith Device isn't removed

                match secondary_device_type_id:
                    case "accelerationSensorSecondary":
                        primary_props["secondaryDeviceAccelerationSensor"] = secondary_dev_id
                    case "humiditySensorSecondary":
                        primary_props["secondaryDeviceHumiditySensor"] = secondary_dev_id
                    case "illuminanceSensorSecondary":
                        primary_props["secondaryDeviceIlluminanceSensor"] = secondary_dev_id
                    case "motionSensorSecondary":
                        primary_props["secondaryDeviceMotionSensor"] = secondary_dev_id
                    case "multiOutletSecondary2":
                        primary_props["secondaryDeviceMultiOutlet2"] = secondary_dev_id
                    case "multiOutletSecondary3":
                        primary_props["secondaryDeviceMultiOutlet3"] = secondary_dev_id
                    case "multiOutletSecondary4":
                        primary_props["secondaryDeviceMultiOutlet4"] = secondary_dev_id
                    case "multiOutletSecondary5":
                        primary_props["secondaryDeviceMultiOutlet5"] = secondary_dev_id
                    case "multiSocketSecondary":
                        primary_props["secondaryDeviceMultiSocket"] = secondary_dev_id
                    case "presenceSensorSecondary":
                        primary_props["secondaryDevicePresenceSensor"] = secondary_dev_id
                    case "pressureSensorSecondary":
                        primary_props["secondaryDevicePressureSensor"] = secondary_dev_id
                    case "temperatureSensorSecondary":
                        primary_props["secondaryDeviceTemperatureSensor"] = secondary_dev_id
                    # case "valveSecondary":
                    #     primary_props["secondaryDeviceValve"] = secondary_dev_id
                    case "voltageSensorSecondary":
                        primary_props["secondaryDeviceVoltageSensor"] = secondary_dev_id

                primary_dev.replacePluginPropsOnServer(primary_props)

                self.optionally_set_indigo_2021_device_sub_type(secondary_dev)

            else:
                secondary_dev = indigo.devices[existing_secondary_devices[secondary_device_type_id]]

                if update_device_name:
                    # TODO: Differentiate for Outlet devices L1 thru L5
                    if hasattr(primary_dev, "subType"):  # If subType property supported for primary device - assume supported on Secondary
                        usp_indigo_name = INDIGO_SUB_TYPE_INFO[secondary_device_type_id][1][0]
                    else:
                        usp_indigo_name = INDIGO_SUB_TYPE_INFO[secondary_device_type_id][1][1]
                    updated_secondary_name = f"{primary_dev.name} [{usp_indigo_name}]"  # Create default name
                    # Check name is unique and if not, make it so
                    desired_indigo_derived_secondary_device_name = updated_secondary_name
                    if updated_secondary_name in indigo.devices and indigo.devices[updated_secondary_name].id != secondary_dev.id:
                        name_check_count = 1
                        while True:
                            check_name = f"{updated_secondary_name}_{name_check_count}"
                            if check_name not in indigo.devices:
                                updated_secondary_name = check_name
                                break
                            name_check_count += 1

                    old_name = secondary_dev.name

                    if desired_indigo_derived_secondary_device_name == updated_secondary_name:  # noqa
                        self.logger.info(f"Indigo secondary Zigbee Device renamed from '{old_name}' to '{desired_indigo_derived_secondary_device_name}'")
                    else:
                        self.logger.warning(f"Indigo secondary Zigbee Device renamed from '{old_name}' to '{updated_secondary_name}' as '{desired_indigo_derived_secondary_device_name}' already in use.")

                    secondary_dev.name = updated_secondary_name  # noqa
                    secondary_dev.replaceOnServer()

                # Special Multi-Socket Processing Start ...

                if secondary_device_type_id == "multiSocketSecondary":
                    secondary_props = secondary_dev.ownerProps
                    supports_energy_meter_cur_power = secondary_props.get("SupportsEnergyMeterCurPower", False)
                    if "uspPowerRight" in primary_props and primary_props["uspPowerRight"]:
                        if not secondary_props.get("SupportsEnergyMeterCurPower", False):
                            supports_energy_meter_cur_power = True
                    else:
                        if secondary_props.get("SupportsEnergyMeterCurPower", False):
                            supports_energy_meter_cur_power = False

                    if secondary_props.get("SupportsEnergyMeterCurPower", False) != supports_energy_meter_cur_power:
                        secondary_props["SupportsEnergyMeterCurPower"] = supports_energy_meter_cur_power
                        secondary_dev.replacePluginPropsOnServer(secondary_props)

                # ... Special Multi-Socket Processing End.

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def publish_zigbee_topic(self, zigbee_coordinator_ieee, friendly_name, topic, payload):
        try:
            # TODO: Check if self.globals[ZC][MQTT_CONNECTED]

            published = False
            for zc_dev_id, zc_dev_details in self.globals[ZC].items():
                # self.globals[ZC][coordinator_dev.id][ZC_IEEE]
                zc_dev = indigo.devices[zc_dev_id]
                if zc_dev.address == zigbee_coordinator_ieee:
                    # if self.globals[ZC][mqtt_broker_device_id][MQTT_PUBLISH_TO_HOMIE]:
                    # topic = "zigbee2mqtt/Outlet 1/set"
                    self.globals[ZC][zc_dev_id][MQTT_CLIENT].publish(topic, payload)
                    published = True
                    # if self.globals[DEBUG]:

            if published:
                self.mqtt_filter_log_processing(zc_dev.name, zigbee_coordinator_ieee, friendly_name, topic, payload)  # noqa
                
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def mqtt_filter_log_processing(self, zc_dev_name, zigbee_coordinator_ieee, topic_friendly_name, topics, payload):
        try:
            log_mqtt_msg = False  # Assume MQTT message should NOT be logged

            # Check if MQTT message filtering required
            if MQTT_FILTERS in self.globals and zigbee_coordinator_ieee in self.globals[MQTT_FILTERS]:
                if len(self.globals[MQTT_FILTERS][zigbee_coordinator_ieee]) > 0 and self.globals[MQTT_FILTERS][zigbee_coordinator_ieee] != ["NONE"]:
                    # As entries exist in the filter list, only log MQTT message for Zigbee device in the filter list
                    if self.globals[MQTT_FILTERS][zigbee_coordinator_ieee] == ["ALL"]:
                        log_mqtt_msg = True
                    else:
                        if topic_friendly_name in self.globals[MQTT_FILTERS][zigbee_coordinator_ieee]:
                            log_mqtt_msg = True

            if log_mqtt_msg:
                self.logger.warning(f">>> Published to '{zc_dev_name}': Topic='{topics}', Payload='{payload}'")  # noqa [unresolved attribute reference]

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
