#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023
#

import logging

# ============================== Custom Imports ===============================
try:
    import indigo  # noqa
except ImportError:
    pass

number = -1

debug_show_constants = False
debug_use_labels = True

# def constant_id(constant_label) -> int:  # Auto increment constant id
def constant_id(constant_label):  # Auto increment constant id

    global number
    if debug_show_constants and number == -1:
        indigo.server.log("Zigbee2MQTT Bridge Plugin internal Constant Name mapping ...", level=logging.DEBUG)
    number += 1
    if debug_show_constants:
        indigo.server.log(f"{number}: {constant_label}", level=logging.DEBUG)
    if debug_use_labels:
        return constant_label
    else:
        return number

# plugin Constants

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

MQTT_ENCRYPTION_PASSWORD_PYTHON_3 = b"indigo_to_zigbee2mqtt"
MQTT_ROOT_TOPIC_DEFAULT = "zigbee2mqtt"

ADDRESS = constant_id("ADDRESS")
API_VERSION = constant_id("API_VERSION")
AVAILABLE = constant_id("AVAILABLE")
CH_EVENT = constant_id("CH_EVENT")
CH_THREAD = constant_id("CH_THREAD")
COLOR_DEBUG = constant_id("COLOR_DEBUG")
DEBUG = constant_id("DEBUG")
HANDLE_ZIGBEE_COORDINATOR_MQTT_TOPIC = constant_id("HANDLE_ZIGBEE_BRIDGE_MQTT_TOPIC")
HANDLE_ZIGBEE_DEVICE_MQTT_TOPIC = constant_id("HANDLE_ZIGBEE_DEVICE_MQTT_TOPIC")
HANDLE_ZIGBEE_GROUP_MQTT_TOPIC = constant_id("HANDLE_ZIGBEE_GROUP_MQTT_TOPIC")
KNOWN_TO_COORDINATOR = constant_id("KNOWN_TO_COORDINATOR")
LOCAL_IP = constant_id("LOCAL_IP")
LOCAL_MAC = constant_id("LOCAL_MAC")
LOCK_ZC = constant_id("LOCK_ZC")
LOCK_ZD_LINKED_INDIGO_DEVICES = constant_id("LOCK_ZD_LINKED_INDIGO_DEVICES")
MQTT = constant_id("MQTT")
MQTT_BROKERS = constant_id("MQTT_BROKERS")
MQTT_CLIENT = constant_id("MQTT_CLIENT")
MQTT_CLIENT_ID = constant_id("MQTT_CLIENT_ID")
MQTT_CLIENT_PREFIX = constant_id("MQTT_CLIENT_PREFIX")
MQTT_CONNECTED = constant_id("MQTT_CONNECTED")
MQTT_CONNECTION_INITIALISED = constant_id("MQTT_CONNECTION_INITIALISED")
MQTT_ENCRYPTION_KEY = constant_id("MQTT_ENCRYPTION_KEY")
MQTT_IP = constant_id("MQTT_IP")
MQTT_FILTERS = constant_id("MQTT_FILTERS")
MQTT_PASSWORD = constant_id("MQTT_PASSWORD")
MQTT_PORT = constant_id("MQTT_PORT")
MQTT_PROCESS_COMMAND_HANDLE_STOP_THREAD = constant_id("MQTT_PROCESS_COMMAND_HANDLE_STOP_THREAD")
MQTT_PROTOCOL = constant_id("MQTT_PROTOCOL")
MQTT_PUBLISH_TO_ZIGBEE2MQTT = constant_id("MQTT_PUBLISH_TO_ZIGBEE2MQTT")
MQTT_ROOT_TOPIC = constant_id("MQTT_ROOT_TOPIC")
MQTT_SUBSCRIBED_TOPICS = constant_id("MQTT_SUBSCRIBED_TOPICS")
MQTT_SUBSCRIBE_TO_ZIGBEE2MQTT = constant_id("MQTT_SUBSCRIBE_TO_ZIGBEE2MQTT")
MQTT_SUPPRESS_IEEE_MISSING = constant_id("MQTT_SUPPRESS_IEEE_MISSING")
MQTT_USERNAME = constant_id("MQTT_USERNAME")
MQTT_ZIGBEE2MQTT_QUEUE = constant_id("MQTT_ZIGBEE2MQTT_QUEUE")
PATH = constant_id("PATH")
PLUGIN_DISPLAY_NAME = constant_id("PLUGIN_DISPLAY_NAME")
PLUGIN_ID = constant_id("PLUGIN_ID")
PLUGIN_INFO = constant_id("PLUGIN_INFO")
PLUGIN_PREFS_FOLDER = constant_id("PLUGIN_PREFS_FOLDER")
PLUGIN_VERSION = constant_id("PLUGIN_VERSION")
QUEUES = constant_id("QUEUES")
ZC = constant_id("ZC [ZIGBEE COORDINATORS]")
ZC_TO_INDIGO_ID = constant_id("ZC_TO_INDIGO_ID")
ZC_LIST = constant_id("ZC_LIST")
ZC_IEEE = constant_id("ZC_IEEE")
ZD = constant_id("ZD [ZIGBEE DEVICE]")
ZD_BATTERY = constant_id("ZD_BATTERY")
ZD_CONTACT = constant_id("ZD_CONTACT")
ZD_DEFINITION = constant_id("ZD_DISABLED")
ZD_DESCRIPTION_HW = constant_id("ZD_DESCRIPTION_HW")
ZD_DESCRIPTION_USER = constant_id("ZD_DESCRIPTION_USER")
ZD_DEVICES = constant_id("ZD_DEVICES")
ZD_DEVICE_DRIVER = constant_id("ZD_DEVICE_DRIVER")
ZD_DEVICE_STATES = constant_id("ZD_DEVICE_STATES")
ZD_DISABLED = constant_id("ZD_DISABLED")
ZD_EXPOSES = constant_id("ZD_EXPOSES")
ZD_FRIENDLY_NAME = constant_id("ZD_FRIENDLY_NAME")
ZD_HUBS = constant_id("ZD_HUBS")
ZD_HUB_EVENT = constant_id("ZD_HUB_EVENT")
ZD_HUB_THREAD = constant_id("ZD_HUB_THREAD")
ZD_HUMIDITY = constant_id("ZD_HUMIDITY")
ZD_INDIGO_DEVICE_ID = constant_id("ZD_INDIGO_DEVICE_ID")
ZD_INDIGO_DEVICE_ID_LIST = constant_id("ZD_INDIGO_DEVICE_ID_LIST")
ZD_INDIGO_HUB_ID = constant_id("ZD_INDIGO_HUB_ID")
ZD_LINKED_INDIGO_DEVICES = constant_id("ZD_LINKED_INDIGO_DEVICES")
ZD_MANUFACTURER = constant_id("ZD_MANUFACTURER")
ZD_MESSAGE_COUNT = constant_id("ZD_MESSAGE_COUNT")
ZD_MODEL = constant_id("ZD_MODEL")
ZD_MODEL_ID = constant_id("ZD_MODEL_ID")
ZD_MOTION = constant_id("ZD_MOTION")
ZD_MQTT_FILTERS = constant_id("ZD_MQTT_FILTERS")
ZD_MQTT_FILTER_DEVICES = constant_id("ZD_MQTT_FILTER_DEVICES")
ZD_MQTT_FILTER_HUB = constant_id("ZD_MQTT_FILTER_HUB")
ZD_OUTLET = constant_id("ZD_OUTLET")
ZD_POWER_SOURCE = constant_id("ZD_POWER_SOURCE")
ZD_PREVIOUS_POWER_LEVEL = constant_id("ZD_PREVIOUS_POWER_LEVEL")
ZD_PREVIOUS_POWER_LEVEL_LEFT = constant_id("ZD_PREVIOUS_POWER_LEVEL_LEFT")
ZD_PREVIOUS_POWER_LEVEL_RIGHT = constant_id("ZD_PREVIOUS_POWER_LEVEL_RIGHT")
ZD_PROPERTIES = constant_id("ZD_PROPERTIES")
ZD_SOFTWARE_BUILD_ID = constant_id("ZD_SOFTWARE_BUILD_ID")
ZD_STATES = constant_id("ZD_STATES")
ZD_STATE_DIM = constant_id("ZD_STATE_DIM")
ZD_STATE_VALVE_LEVEL = constant_id("ZD_STATE_VALVE_LEVEL")
ZD_TEMPERATURE = constant_id("ZD_TEMPERATURE")
ZD_TO_INDIGO_ID = constant_id("ZD_TO_INDIGO_ID")
ZD_VENDOR = constant_id("ZD_VENDOR")
ZH_EVENT = constant_id("ZH_EVENT")
ZH_THREAD = constant_id("ZH_THREAD")
ZIGBEE2MQTT_ROOT_TOPIC = constant_id("ZIGBEE2MQTT_ROOT_TOPIC")

ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES = dict()
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["acceleration"] = ["humiditySensor", "illuminanceSensor", "motionSensor", "multiSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["battery"] = ["button", "contactSensor", "humiditySensor", "illuminanceSensor",
                                                      "motionSensor", "multiSensor", "remoteAudio", "remoteDimmer", "temperatureSensor", "thermostat",
                                                      "vibrationSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["action"] = ["button", "remoteAudio", "remoteDimmer", "vibrationSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["angles"] = ["vibrationSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["brightness"] = ["dimmer"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["color_mode"] = ["dimmer"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["color"] = ["dimmer"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["color_temp"] = ["dimmer"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["contact"] = ["contactSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["dim"] = ["thermostat"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["energy"] = ["outlet"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["humidity"] = ["humiditySensor", "illuminanceSensor", "motionSensor", "multiSensor", "temperatureSensor", "thermostat"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["illuminance"] = ["humiditySensor", "illuminanceSensor", "motionSensor", "multiSensor", "radarSensor", "temperatureSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["mode"] = ["thermostat"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["linkquality"] = ["blind", "button", "contactSensor", "dimmer", "humiditySensor", "illuminanceSensor",
                                                           "motionSensor", "multiOutlet", "multiSensor", "multiSocket",
                                                           "presenceSensor", "outlet", "radarSensor",
                                                           "temperatureSensor", "thermostat", "vibrationSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["occupancy"] = ["humiditySensor", "illuminanceSensor", "motionSensor", "multiSensor", "temperatureSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["position"] = ["blind"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["power"] = ["outlet"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["power_left"] = ["multiSocket"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["power_right"] = ["multiSocket"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["presence"] = ["button", "contactSensor", "motionSensor", "multiSensor", "presenceSensor", "outlet", "temperatureSensor", "radarSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["presence_event"] = ["radarSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["presence-sensor"] = ["button", "contactSensor", "motionSensor", "multiSensor", "outlet", "presenceSensor", "temperatureSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["pressure"] = ["multiSensor", "temperatureSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["state"] = ["blind"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["state_l1"] = ["multiOutlet"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["state_l2"] = ["multiOutlet"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["state_l3"] = ["multiOutlet"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["state_l4"] = ["multiOutlet"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["state_l5"] = ["multiOutlet"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["state_left"] = ["multiSocket"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["state_right"] = ["multiSocket"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["strength"] = ["vibrationSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["onoff"] = ["dimmer", "thermostat", "outlet"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["tamper"] = ["motionSensor", "multiSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["temperature"] = ["blind", "humiditySensor", "illuminanceSensor", "motionSensor", "multiSensor", "radarSensor", "temperatureSensor", "thermostat"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["thermostat-setpoint"] = ["thermostat"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["vibration"] = ["vibrationSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["voltage"] = ["button", "contactSensor", "motionSensor", "outlet", "temperatureSensor", "vibrationSensor"]
ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["refresh"] = ["outlet", "thermostat"]

ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES = dict()
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["button"] = ["action"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["blind"] = ["position"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["contactSensor"] = ["contact"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["dimmer"] = ["state"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["humiditySensor"] = ["humidity"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["illuminanceSensor"] = ["illuminance"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["motionSensor"] = ["motion"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["multiOutlet"] = ["state_l1"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["multiSensor"] = ["motion"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["multiSocket"] = ["state_left"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["outlet"] = ["onoff"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["presenceSensor"] = ["presence"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["radarSensor"] = ["radar"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["remoteAudio"] = ["action"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["remoteDimmer"] = ["action"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["temperatureSensor"] = ["temperature"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["thermostat"] = ["temperature"]
ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES["vibrationSensor"] = ["vibration"]

ZG = constant_id("ZG [ZIGBEE Group]")
ZG_FRIENDLY_NAME = constant_id("ZG_FRIENDLY_NAME")
ZG_ID = constant_id("ZG_ID")
ZG_MEMBERS = constant_id("ZG_MEMBERS")
ZG_INDIGO_DEVICE_ID = constant_id("ZG_INDIGO_DEVICE_ID")

ZS = constant_id("ZS [ZIGBEE Scene]")

INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE = "0"
INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE = "1"
INDIGO_SECONDARY_DEVICE = "2"
INDIGO_SECONDARY_DEVICE_ADDITIONAL_STATE = "3"

INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE = dict()
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["blind"] = ["temperatureSensorSecondary"]
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["button"] = ["voltageSensorSecondary"]
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["contactSensor"] = ["voltageSensorSecondary"]
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["dimmer"] = []
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["humiditySensor"] = ["accelerationSensorSecondary", "illuminanceSensorSecondary", "motionSensorSecondary", "pressureSensorSecondary", "temperatureSensorSecondary"]
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["illuminanceSensor"] = ["accelerationSensorSecondary", "humiditySensorSecondary", "motionSensorSecondary", "pressureSensorSecondary", "temperatureSensorSecondary"]
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["motionSensor"] = ["accelerationSensorSecondary", "humiditySensorSecondary", "illuminanceSensorSecondary", "temperatureSensorSecondary"]


INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["multiOutlet"] = ["voltageSensorSecondary", "multiOutletSecondary2", "multiOutletSecondary3", "multiOutletSecondary4", "multiOutletSecondary5"]

INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["multiSensor"] = ["accelerationSensorSecondary", "humiditySensorSecondary", "illuminanceSensorSecondary", "temperatureSensorSecondary"]

INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["multiSocket"] = ["multiSocketSecondary"]

INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["outlet"] = ["voltageSensorSecondary"]

INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["presenceSensor"] = []
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["radarSensor"] = ["temperatureSensorSecondary"]
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["temperatureSensor"] = ["humiditySensorSecondary", "illuminanceSensorSecondary", "motionSensorSecondary", "pressureSensorSecondary", "voltageSensorSecondary"]
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["thermostat"] = ["valveSecondary"]
INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE["vibrationSensor"] = []

INDIGO_SUB_TYPE_INFO = dict()
INDIGO_SUB_TYPE_INFO["accelerationSensorSecondary"] = ["uspAccelerationIndigo", [indigo.kSensorDeviceSubType.Tamper, "Acceleration"],
                                                       [("SupportsOnState", True), ("AllowOnStateChange", True), ("SupportsStatusRequest", False),
                                                        ("SupportsSensorValue", False), ("AllowSensorValueChange", False)]]
INDIGO_SUB_TYPE_INFO["illuminanceSensorSecondary"] = ["uspIlluminanceIndigo", [indigo.kSensorDeviceSubType.Illuminance, "Illuminance"],
                                                      [("SupportsOnState", False), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                       ("SupportsSensorValue", True), ("AllowSensorValueChange", False)]]
INDIGO_SUB_TYPE_INFO["humiditySensorSecondary"] = ["uspHumidityIndigo", [indigo.kSensorDeviceSubType.Humidity, "Humidity"],
                                                   [("SupportsOnState", False), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                    ("SupportsSensorValue", True), ("AllowSensorValueChange", False)]]
INDIGO_SUB_TYPE_INFO["motionSensorSecondary"] = ["uspMotionIndigo", [indigo.kSensorDeviceSubType.Motion, "Motion"],
                                                 [("SupportsOnState", True), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                  ("SupportsSensorValue", False), ("AllowSensorValueChange", False)]]

INDIGO_SUB_TYPE_INFO["multiOutletSecondary2"] = ["uspStateL2Indigo", [indigo.kRelayDeviceSubType.Outlet, "Outlet L2"],
                                                 [("SupportsOnState", True), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                  ("SupportsSensorValue", False), ("AllowSensorValueChange", False)]]

INDIGO_SUB_TYPE_INFO["multiOutletSecondary3"] = ["uspStateL3Indigo", [indigo.kRelayDeviceSubType.Outlet, "Outlet L3"],
                                                 [("SupportsOnState", True), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                  ("SupportsSensorValue", False), ("AllowSensorValueChange", False)]]

INDIGO_SUB_TYPE_INFO["multiOutletSecondary4"] = ["uspStateL4Indigo", [indigo.kRelayDeviceSubType.Outlet, "Outlet L4"],
                                                 [("SupportsOnState", True), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                  ("SupportsSensorValue", False), ("AllowSensorValueChange", False)]]

INDIGO_SUB_TYPE_INFO["multiOutletSecondary5"] = ["uspStateL5Indigo", [indigo.kRelayDeviceSubType.Outlet, "Outlet L5"],
                                                 [("SupportsOnState", True), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                  ("SupportsSensorValue", False), ("AllowSensorValueChange", False)]]

INDIGO_SUB_TYPE_INFO["multiSocketSecondary"] = ["uspStateRightIndigo", [indigo.kRelayDeviceSubType.Outlet, "Socket Right"],
                                                 [("SupportsOnState", True), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                  ("SupportsSensorValue", False), ("AllowSensorValueChange", False)]]

INDIGO_SUB_TYPE_INFO["pressureSensorSecondary"] = ["uspPressureIndigo", [indigo.kSensorDeviceSubType.Pressure, "Pressure"],
                                                   [("SupportsOnState", False), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                    ("SupportsSensorValue", True), ("AllowSensorValueChange", False)]]
INDIGO_SUB_TYPE_INFO["temperatureSensorSecondary"] = ["uspTemperatureIndigo", [indigo.kSensorDeviceSubType.Temperature, "Temperature"],
                                                      [("SupportsOnState", False), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                                       ("SupportsSensorValue", True), ("AllowSensorValueChange", False)]]
INDIGO_SUB_TYPE_INFO["valveSecondary"] = ["uspValveIndigo", [indigo.kDimmerDeviceSubType.Valve, "Valve"], [("SupportsStatusRequest", True)]]
INDIGO_SUB_TYPE_INFO["voltageSensorSecondary"] = ["uspVoltageIndigo", [indigo.kSensorDeviceSubType.Voltage, "Voltage"],
                                            [("SupportsOnState", False), ("AllowOnStateChange", False), ("SupportsStatusRequest", False),
                                             ("SupportsSensorValue", True), ("AllowSensorValueChange", False)]]

INDIGO_PRIMARY_DEVICE_INFO = dict()
INDIGO_PRIMARY_DEVICE_INFO["button"] = [indigo.kRelayDeviceSubType.PlugIn, "Button"]
INDIGO_PRIMARY_DEVICE_INFO["blind"] = [indigo.kDimmerDeviceSubType.Dimmer, "Blind"]
INDIGO_PRIMARY_DEVICE_INFO["contactSensor"] = [indigo.kSensorDeviceSubType.DoorWindow, "Contact"]
INDIGO_PRIMARY_DEVICE_INFO["dimmer"] = [indigo.kDimmerDeviceSubType.Dimmer, "Dimmer"]
INDIGO_PRIMARY_DEVICE_INFO["humidity"] = [indigo.kSensorDeviceSubType.Humidity, "Humidity"]
INDIGO_PRIMARY_DEVICE_INFO["illuminance"] = [indigo.kSensorDeviceSubType.Illuminance, "Illuminance"]
INDIGO_PRIMARY_DEVICE_INFO["motionSensor"] = [indigo.kSensorDeviceSubType.Motion, "Motion"]
INDIGO_PRIMARY_DEVICE_INFO["outlet"] = [indigo.kRelayDeviceSubType.Outlet, "Outlet"]
INDIGO_PRIMARY_DEVICE_INFO["multiOutlet"] = [indigo.kRelayDeviceSubType.Outlet, "Multi-Outlet"]
INDIGO_PRIMARY_DEVICE_INFO["multiSensor"] = [indigo.kSensorDeviceSubType.Motion, "Motion"]
INDIGO_PRIMARY_DEVICE_INFO["multiSocket"] = [indigo.kRelayDeviceSubType.Outlet, "Multi-Socket"]
INDIGO_PRIMARY_DEVICE_INFO["presenceSensor"] = [indigo.kSensorDeviceSubType.Presence, "Presence"]
INDIGO_PRIMARY_DEVICE_INFO["radarSensor"] = [indigo.kSensorDeviceSubType.Presence, "Presence"]
INDIGO_PRIMARY_DEVICE_INFO["remoteAudio"] = [indigo.kDeviceSubType.Remote, "Remote [Audio]"]
INDIGO_PRIMARY_DEVICE_INFO["remoteDimmer"] = [indigo.kDeviceSubType.Remote, "Remote [Dimmer]"]
INDIGO_PRIMARY_DEVICE_INFO["temperatureSensor"] = [indigo.kSensorDeviceSubType.Temperature, "Temperature"]
INDIGO_PRIMARY_DEVICE_INFO["thermostat"] = [indigo.kSensorDeviceSubType.Temperature, "Thermostat"]
INDIGO_PRIMARY_DEVICE_INFO["vibrationSensor"] = [indigo.kSensorDeviceSubType.Vibration, "Vibration"]
INDIGO_PRIMARY_DEVICE_INFO["zigbeeCoordinator"] = [indigo.kDeviceSubType.Other, "Coordinator"]

INDIGO_ONE_SPACE_BEFORE_UNITS = True
INDIGO_NO_SPACE_BEFORE_UNITS = False

LOG_LEVEL_NOT_SET = 0
LOG_LEVEL_DEBUGGING = 10
LOG_LEVEL_TOPIC = 15
LOG_LEVEL_INFO = 20
LOG_LEVEL_WARNING = 30
LOG_LEVEL_ERROR = 40
LOG_LEVEL_CRITICAL = 50

LOG_LEVEL_TRANSLATION = dict()
LOG_LEVEL_TRANSLATION[LOG_LEVEL_NOT_SET] = "Not Set"
LOG_LEVEL_TRANSLATION[LOG_LEVEL_DEBUGGING] = "Topic Filter Logging"
LOG_LEVEL_TRANSLATION[LOG_LEVEL_INFO] = "Info"
LOG_LEVEL_TRANSLATION[LOG_LEVEL_WARNING] = "Warning"
LOG_LEVEL_TRANSLATION[LOG_LEVEL_ERROR] = "Error"
LOG_LEVEL_TRANSLATION[LOG_LEVEL_CRITICAL] = "Critical"

# QUEUE Priorities
QUEUE_PRIORITY_STOP_THREAD    = 0
QUEUE_PRIORITY_COMMAND_HIGH   = 100
QUEUE_PRIORITY_COMMAND_MEDIUM = 200
QUEUE_PRIORITY_POLLING        = 300
QUEUE_PRIORITY_LOW            = 400

# Rounded  Kelvin Descriptions (from iOS LIFX App)
ROUNDED_KELVINS =dict()
ROUNDED_KELVINS[1500] = ((246, 221, 184), "~ Candlelight")  # TODO: Set correct RGB values
ROUNDED_KELVINS[2000] = ((246, 221, 184), "~ Sunset")  # TODO: Set correct RGB values
ROUNDED_KELVINS[2500] = ((246, 221, 184), "~ Ultra Warm")
ROUNDED_KELVINS[2750] = ((246, 224, 184), "~ Incandescent")
ROUNDED_KELVINS[3000] = ((248, 227, 195), "~ Warm")
ROUNDED_KELVINS[3200] = ((247, 228, 198), "~ Neutral Warm")
ROUNDED_KELVINS[3500] = ((246, 228, 201), "~ Neutral")
ROUNDED_KELVINS[4000] = ((249, 234, 210), "~ Cool")
ROUNDED_KELVINS[4500] = ((250, 238, 217), "~ Cool Daylight")
ROUNDED_KELVINS[5000] = ((250, 239, 219), "~ Soft Daylight")
ROUNDED_KELVINS[5500] = ((249, 240, 225), "~ Daylight")
ROUNDED_KELVINS[6000] = ((247, 241, 230), "~ Noon Daylight")
ROUNDED_KELVINS[6500] = ((245, 242, 234), "~ Bright Daylight")
ROUNDED_KELVINS[7000] = ((241, 240, 236), "~ Cloudy Daylight")
ROUNDED_KELVINS[7500] = ((236, 236, 238), "~ Blue Daylight")
ROUNDED_KELVINS[8000] = ((237, 240, 246), "~ Blue Overcast")
ROUNDED_KELVINS[8500] = ((236, 241, 249), "~ Blue Water")
ROUNDED_KELVINS[9000] = ((237, 243, 252), "~ Blue Ice")
