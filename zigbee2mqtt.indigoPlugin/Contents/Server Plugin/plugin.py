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
from cryptography.fernet import Fernet  # noqa
from cryptography.hazmat.primitives import hashes  # noqa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # noqa
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
from zigbeeHandler import ThreadZigbeeHandler

# Mixin imports for refactored plugin modules
from plugin_actions import ActionsMixin
from plugin_color_control import ColorControlMixin
from plugin_config_ui import ConfigUIMixin
from plugin_device_lifecycle import DeviceLifecycleMixin
from plugin_list_generators import ListGeneratorsMixin
from plugin_mqtt import MQTTMixin
from plugin_secondary_devices import SecondaryDevicesMixin
from plugin_state_list import StateListMixin

import_errors = []
try:
    import paho.mqtt.client as mqtt
except ImportError:
    import_errors.append("paho-mqtt")

try:
    from colormath.color_objects import XYZColor, sRGBColor, xyYColor
    from colormath.color_conversions import convert_color
except ImportError:
    import_errors.append("colormath")


# ================================== Header ===================================
__author__    = "Autolog"
__copyright__ = ""
__license__   = "MIT"
__build__     = "unused"
__title__     = "Zigbee2mqtt Bridge Plugin for Indigo"
__version__   = "unused"

from cryptography_support import decode, encode


# noinspection PyPep8Naming
class Plugin(ActionsMixin,
             ColorControlMixin,
             ConfigUIMixin,
             DeviceLifecycleMixin,
             ListGeneratorsMixin,
             MQTTMixin,
             SecondaryDevicesMixin,
             StateListMixin,
             indigo.PluginBase):

    def __init__(self, plugin_id, plugin_display_name, plugin_version, plugin_prefs):
        super(Plugin, self).__init__(plugin_id, plugin_display_name, plugin_version, plugin_prefs)

        # logging.addLevelName(LOG_LEVEL_TOPIC, "topic")

        # def topic(self, message, *args, **kws):  # noqa [Shadowing names from outer scope = self]
        #     # if self.isEnabledFor(LOG_LEVEL_TOPIC):
        #     # Yes, logger takes its '*args' as 'args'.
        #     self.log(LOG_LEVEL_TOPIC, message, *args, **kws)
        #
        # logging.Logger.topic = topic

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

        self.globals[ZC] = dict()  # Dictionary of  Zigbee Coordinators - keyed on Indigo Device ID
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
        log_message = f"'{exception_error_message}' in module '{module[-1]}', method '{method} [{self.globals[PLUGIN_INFO][PLUGIN_VERSION]}]'"
        if log_failing_statement:
            log_message = log_message + f"\n   Failing statement [line {line_number}]: '{statement}'"
        else:
            log_message = log_message + f" at line {line_number}"
        self.logger.error(log_message)

    def shutdown(self):

        self.logger.info("Zigbee2mqtt Bridge plugin shutdown invoked")

    def startup(self):
        try:
            if len(import_errors):
                stop_message = "Plugin startup cancelled due to one or more required plugin Python libraries missing:\n"
                for package in import_errors:
                    stop_message = f"{stop_message}      - {package}\n"
                return stop_message

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
                                self.globals[ZD][zigbee_coordinator_ieee][dev.address][ZD_MESSAGE_COUNT] = 0
                                self.globals[ZD_TO_INDIGO_ID][dev.address] = dev.id  # Zigbee device to primary Indigo device

        except Exception as exception_error:
                self.exception_handler(exception_error, True)  # Log error and display failing statement

    def stop_concurrent_thread(self):
        self.logger.info("Zigbee2mqtt Bridge plugin closing down")

