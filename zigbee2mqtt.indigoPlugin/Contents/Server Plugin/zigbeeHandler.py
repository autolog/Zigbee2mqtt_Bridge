#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023
#

try:
    from colormath.color_objects import XYZColor, sRGBColor, xyYColor
    from colormath.color_conversions import convert_color
except ImportError:
    pass

import colorsys
import datetime
try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass
import json
import queue
import sys
import threading
import traceback

from constants import *


def _no_image():
    try:
        return getattr(indigo.kStateImageSel, "NoImage")  # Python 3
    except AttributeError:
        return getattr(indigo.kStateImageSel, "None")  # Python 2


# noinspection PyPep8Naming
class ThreadZigbeeHandler(threading.Thread):

    # This class handles Zigbee Coordinator processing

    def __init__(self, pluginGlobals, event, zc_dev_id):
        try:
            threading.Thread.__init__(self)

            self.globals = pluginGlobals
            self.zc_dev_id = zc_dev_id
            self.zc_address = indigo.devices[self.zc_dev_id].address

            self.key_value_lists = dict()

            self.timers = dict()

            self.zigbee_devices_offline = dict()

            self.zigbeeLogger = logging.getLogger("Plugin.Zigbee")

            self.properties_set = {"battery", "linkquality"}  # Starter for 10 for compiling a list of properties for documenting all discovered properties

            self.threadStop = event

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def exception_handler(self, exception_error_message, log_failing_statement):
        filename, line_number, method, statement = traceback.extract_tb(sys.exc_info()[2])[-1]  # noqa [Ignore duplicate code warning]
        module = filename.split('/')
        log_message = f"'{exception_error_message}' in module '{module[-1]}', method '{method} [{self.globals[PLUGIN_INFO][PLUGIN_VERSION]}]'"
        if log_failing_statement:
            log_message = log_message + f"\n   Failing statement [line {line_number}]: '{statement}'"
        else:
            log_message = log_message + f" at line {line_number}"
        self.zigbeeLogger.error(log_message)

    def run(self):
        try:
            while not self.threadStop.is_set():
                try:
                    mqtt_message_sequence, zigbee_process_command, zc_dev_id, mqtt_topics, mqtt_topics_list, mqtt_payload = self.globals[QUEUES][MQTT_ZIGBEE2MQTT_QUEUE][self.zc_dev_id].get(True, 5)

                    if zigbee_process_command == HANDLE_ZIGBEE_DEVICE_MQTT_TOPIC:
                        self.handle_zigbee_device_topics(zc_dev_id, mqtt_topics, mqtt_topics_list, mqtt_payload)
                    elif zigbee_process_command == HANDLE_ZIGBEE_COORDINATOR_MQTT_TOPIC:
                        # if self.globals[DEBUG]: self.zigbeeLogger.error(f"=========== > ZIGBEE COORDINATOR TOPIC: {mqtt_topics}")
                        self.handle_zigebee_coordinator_topics(zc_dev_id, mqtt_topics, mqtt_topics_list, mqtt_payload)
                    elif zigbee_process_command == HANDLE_ZIGBEE_GROUP_MQTT_TOPIC:
                        self.handle_zigebee_group_topics(zc_dev_id, mqtt_topics, mqtt_topics_list, mqtt_payload)
                except queue.Empty:
                    pass
                except Exception as exception_error:
                    self.exception_handler(exception_error, True)  # Log error and display failing statement
            else:
                pass
                # TODO: At this point, queue a recovery for n seconds time
                # TODO: In the meanwhile, just disable and then enable the Indigo Zigbee Coordinator device

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def handle_zigebee_coordinator_topics(self, zc_dev_id, topics, topics_list, payload):
        # print(f"Payload Type: {type(payload)}")
        try:
            # self.zigbeeLogger.error(f"Zigbee Coordinator: Topic={topics}")

            coordinator_topic = topics_list[2]
            # self.zigbeeLogger.error(f"Zigbee Coordinator: Coordinator Topic={coordinator_topic}")
            if coordinator_topic == "config":
                self.handle_zigebee_coordinator_topic_config(zc_dev_id, topics, topics_list, payload)
            elif coordinator_topic == "devices":
                self.handle_zigebee_coordinator_topic_devices(zc_dev_id, topics, topics_list, payload)
            elif coordinator_topic == "extensions":
                pass
            elif coordinator_topic == "groups":
                self.handle_zigebee_coordinator_topic_groups(zc_dev_id, topics, topics_list, payload)
            elif coordinator_topic == "info":
                pass
            elif coordinator_topic == "logging":
                pass
            elif coordinator_topic == "state":
                pass

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def handle_zigebee_coordinator_topic_config(self, zc_dev_id, topics, topics_list, payload):
        try:
            # json_payload = json.loads(payload)
            pass
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def handle_zigebee_coordinator_topic_devices(self, zc_dev_id, topics, topics_list, payload):
        try:
            zc_dev = indigo.devices[zc_dev_id]
            if not zc_dev.enabled:
                return

            json_payload = json.loads(payload)

            zigbee_coordinator_ieee = ""
            for zigbee_device in json_payload:
                if zigbee_device['type'] == "Coordinator":
                    zigbee_coordinator_ieee = zigbee_device['ieee_address']
                    if zigbee_coordinator_ieee not in self.globals[ZD]:
                        self.globals[ZD][zigbee_coordinator_ieee] = dict()
                    coordinator_dev = indigo.devices[zc_dev_id]
                    coordinator_dev_props = coordinator_dev.pluginProps
                    if coordinator_dev.address != zigbee_coordinator_ieee:
                        self.zigbeeLogger.warning(f"Indigo Zigbee Coordinator Device {coordinator_dev.name} address updated from '{coordinator_dev.address} to '{zigbee_coordinator_ieee}")
                        coordinator_dev_props["address"] = zigbee_coordinator_ieee
                        coordinator_dev.replacePluginPropsOnServer(coordinator_dev_props)

                        for zc_ieee, indigo_id in self.globals[ZC_TO_INDIGO_ID].items():
                            if indigo_id == coordinator_dev.id:
                                del self.globals[ZC_TO_INDIGO_ID][zc_ieee]
                                break
                        if zigbee_coordinator_ieee != "":
                            self.globals[ZC][coordinator_dev.id][ZC_IEEE] = zigbee_coordinator_ieee
                            self.globals[ZC_TO_INDIGO_ID][zigbee_coordinator_ieee] = coordinator_dev.id

                        if self.globals[DEBUG]: self.zigbeeLogger.error(f"ZIGBEE COORDINATORS: {self.globals[ZC_TO_INDIGO_ID]}")
                    coordinator_dev.updateStateOnServer("topicFriendlyName", "bridge")

                elif (zigbee_device['type'] == "EndDevice" or zigbee_device['type'] == "Router") and zigbee_coordinator_ieee != "":

                    zigbee_device_ieee = zigbee_device['ieee_address']
                    if zigbee_device_ieee not in self.globals[ZD][zigbee_coordinator_ieee]:
                        self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee] = dict()

                    # Default to the Indigo Device Id associated with this Zigbee device to zero if not setup
                    if ZD_INDIGO_DEVICE_ID not in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                        self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] = 0

                    # Now store rest of the device details from the coordinator Bridge mqtt message in the global store
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] = zigbee_device['friendly_name']

                    if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] != 0:
                        zd_dev_id = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID]
                        if zd_dev_id in indigo.devices:
                            zd_dev = indigo.devices[zd_dev_id]
                            if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] != zd_dev.states["topicFriendlyName"]:
                                zd_dev.updateStateOnServer("topicFriendlyName", self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME])

                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MANUFACTURER] = zigbee_device.get('manufacturer', "")
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MODEL_ID] = zigbee_device.get("model_id", "")
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_POWER_SOURCE] = zigbee_device.get("power_source", "")
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DESCRIPTION_USER] = zigbee_device.get("description", "")
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DISABLED] = zigbee_device.get("disabled", "")
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_SOFTWARE_BUILD_ID] = zigbee_device.get("software_build_id", "")

                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION] = dict()
                    zigbee_device_definition = zigbee_device['definition']
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_DESCRIPTION_HW] = zigbee_device_definition["description"]
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_VENDOR] = zigbee_device_definition["vendor"]
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_MODEL] = zigbee_device_definition["model"]

                    # self.zigbeeLogger.warning(f"ZD_DEFINITION: Description='{zigbee_device_definition['description']}', Vendor='{zigbee_device_definition['vendor']}', Model='{zigbee_device_definition['model']}'")

                    # Store the exposes array of properties from the coordinator Bridge mqtt message in the global store
                    # So there is a full record of the individual properties capabilities. TODO: Reserved for future use
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_EXPOSES] = zigbee_device_definition["exposes"]  # List of dicts

                    properties = list()
                    properties_message = ""  # To log to the Indigo Event Log (during testing)
                    for zigbee_device_property_dict in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_EXPOSES]:
                        if "features" in zigbee_device_property_dict:
                            # endpoint = zigbee_device_property_dict.get("endpoint", "")
                            # endpoint = f" [{endpoint}]" if endpoint != "" else "xyz"
                            for zigbee_device_features_property_dict in zigbee_device_property_dict["features"]:
                                if "property" in zigbee_device_features_property_dict:
                                    # property_endpoint = f"{zigbee_device_features_property_dict['property']}{endpoint}"
                                    property_endpoint = f"{zigbee_device_features_property_dict['property']}"
                                    properties.append(property_endpoint)
                                    self.properties_set.add(zigbee_device_features_property_dict['property'])  # This Python set is used to record all properties
                                    properties_message += f", {zigbee_device_features_property_dict['property']}"
                                    if zigbee_device_features_property_dict['property'] == "state":
                                        additional_property = "onoff"
                                        properties.append(additional_property)
                                        self.properties_set.add(additional_property)  # This Python set is used to record all properties
                                        properties_message += f", {additional_property}"

                        elif "property" in zigbee_device_property_dict:
                            properties.append(zigbee_device_property_dict['property'])
                            self.properties_set.add(zigbee_device_property_dict['property'])  # This Python set is used to record all properties
                            properties_message += f", {zigbee_device_property_dict['property']}"
                            if zigbee_device_property_dict['property'] == "state":
                                additional_property = "onoff"
                                properties.append(additional_property)
                                self.properties_set.add(additional_property)  # This Python set is used to record all properties
                                properties_message += f", {additional_property}"
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_PROPERTIES] = properties  # Store properties list in Globals for this zigbee device
                    properties_message = properties_message[2:]  # Removes ", " at start (if present)
                    if self.globals[DEBUG]:
                        self.zigbeeLogger.info(
                        f"Zigbee Device [{zigbee_device['ieee_address']} | {zigbee_device_definition['description']}]: {zigbee_device['friendly_name']} [{zigbee_device_definition['vendor']} - {zigbee_device_definition['model']}]\nProperties: {properties_message}")

                    # if zigbee_device_ieee not in indigo.devices:
                    #     self.globals[ZC][AVAILABLE][zigbee_device_ieee] = True
                    #     continue

                    # At this point there is a an Indigo device for the zigbee device, so update its details
                    # TODO: update device states and props
                else:
                    if self.globals[DEBUG]: self.zigbeeLogger.error(f"UNKNOWN DEVICE TYPE: {zigbee_device['type']}, Details ...\n{payload}")

            # # TESTING Aqara E1 2 gang switch (with neutral) - START ...
            # test_aqara_e1 = False
            # if test_aqara_e1:
            #     aqara_e1_ieee = "0x54ef4410006804af"
            #     zigbee_device_ieee = aqara_e1_ieee
            #     if zigbee_device_ieee not in self.globals[ZD][zigbee_coordinator_ieee]:
            #         self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee] = dict()
            #
            #     # Default to the Indigo Device Id associated with this Zigbee device to zero if not setup
            #     if ZD_INDIGO_DEVICE_ID not in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
            #         self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] = 0
            #
            #     # Now store rest of the device details from the coordinator Bridge mqtt message in the global store
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] = "Study/Aqara E1 Switch"
            #
            #     if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] != 0:
            #         zd_dev_id = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID]
            #         if zd_dev_id in indigo.devices:
            #             zd_dev = indigo.devices[zd_dev_id]
            #             if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] != zd_dev.states["topicFriendlyName"]:
            #                 zd_dev.updateStateOnServer("topicFriendlyName", self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME])
            #
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MANUFACTURER] = "LUMI"  # zigbee_device.get('manufacturer', "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MODEL_ID] = ""  # zigbee_device.get("model_id", "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_POWER_SOURCE] = "Mains (single phase)"  # zigbee_device.get("power_source", "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DESCRIPTION_USER] = ""  # zigbee_device.get("description", "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DISABLED] = ""  # zigbee_device.get("disabled", "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_SOFTWARE_BUILD_ID] = ""  # zigbee_device.get("software_build_id", "")
            #
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION] = dict()
            #     # zigbee_device_definition = zigbee_device['definition']
            #
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_DESCRIPTION_HW] = "Aqara E1 2 gang switch (with neutral)"  # zigbee_device_definition["description"]
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_VENDOR] = "Lumi"  # zigbee_device_definition["vendor"]
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_MODEL] = "QBKG41LM"  # zigbee_device_definition["model"]
            #
            #     aqara_e1_properties = ["linkquality",
            #                            "action", "device_temperature",
            #                            "state_left", "state_right"]
            #     self.globals[ZD][zigbee_coordinator_ieee][aqara_e1_ieee][ZD_PROPERTIES] = aqara_e1_properties  # Store properties list in Globals for this zigbee device
            #     self.properties_set.add("linkquality")
            #     self.properties_set.add("action")
            #     self.properties_set.add("device_temperature")
            #     self.properties_set.add("state_left")
            #     self.properties_set.add("state_right")
            # # TESTING Aqara E1 2 gang switch (with neutral) - ... END

            # # TESTING Aqara E1 single gang switch (with neutral) - START ...
            # test_aqara_e1_single = False
            # if test_aqara_e1_single:
            #     aqara_e1_ieee = "0x54ef44100065b6ef"
            #     zigbee_device_ieee = aqara_e1_ieee
            #     if zigbee_device_ieee not in self.globals[ZD][zigbee_coordinator_ieee]:
            #         self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee] = dict()
            #
            #     # Default to the Indigo Device Id associated with this Zigbee device to zero if not setup
            #     if ZD_INDIGO_DEVICE_ID not in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
            #         self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] = 0
            #
            #     # Now store rest of the device details from the coordinator Bridge mqtt message in the global store
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] = "Study/Aqara E1 Single Switch"
            #
            #     if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] != 0:
            #         zd_dev_id = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID]
            #         if zd_dev_id in indigo.devices:
            #             zd_dev = indigo.devices[zd_dev_id]
            #             if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] != zd_dev.states["topicFriendlyName"]:
            #                 zd_dev.updateStateOnServer("topicFriendlyName", self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME])
            #
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MANUFACTURER] = "LUMI"  # zigbee_device.get('manufacturer', "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MODEL_ID] = ""  # zigbee_device.get("model_id", "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_POWER_SOURCE] = "Mains (single phase)"  # zigbee_device.get("power_source", "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DESCRIPTION_USER] = ""  # zigbee_device.get("description", "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DISABLED] = ""  # zigbee_device.get("disabled", "")
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_SOFTWARE_BUILD_ID] = ""  # zigbee_device.get("software_build_id", "")
            #
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION] = dict()
            #     # zigbee_device_definition = zigbee_device['definition']
            #
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_DESCRIPTION_HW] = "Aqara E1 single gang switch (with neutral)"  # zigbee_device_definition["description"]
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_VENDOR] = "Lumi"  # zigbee_device_definition["vendor"]
            #     self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_MODEL] = "QBKG40LM"  # zigbee_device_definition["model"]
            #
            #     aqara_e1_properties = ["linkquality",
            #                            "action", "device_temperature",
            #                            "state"]
            #     self.globals[ZD][zigbee_coordinator_ieee][aqara_e1_ieee][ZD_PROPERTIES] = aqara_e1_properties  # Store properties list in Globals for this zigbee device
            #     self.properties_set.add("linkquality")
            #     self.properties_set.add("action")
            #     self.properties_set.add("device_temperature")
            #     self.properties_set.add("state")
            #
            # # TESTING Aqara E1 single gang switch (with neutral) - ... END

            # TESTING Tuya Dimmer Module - START ...
            test_tuya_dimmer_module = True
            if test_tuya_dimmer_module:
                tuya_dimmer_module_ieee = "0x123456789"
                zigbee_device_ieee = tuya_dimmer_module_ieee
                if zigbee_device_ieee not in self.globals[ZD][zigbee_coordinator_ieee]:
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee] = dict()

                # Default to the Indigo Device Id associated with this Zigbee device to zero if not setup
                if ZD_INDIGO_DEVICE_ID not in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] = 0

                # Now store rest of the device details from the coordinator Bridge mqtt message in the global store
                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] = "Study/Tuya Dimmer Module"

                if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] != 0:
                    zd_dev_id = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID]
                    if zd_dev_id in indigo.devices:
                        zd_dev = indigo.devices[zd_dev_id]
                        if "topicFriendlyName" not in zd_dev.states or self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] != zd_dev.states["topicFriendlyName"]:
                            zd_dev.updateStateOnServer("topicFriendlyName", self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME])

                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MANUFACTURER] = "Tuya"  # zigbee_device.get('manufacturer', "")
                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MODEL_ID] = ""  # zigbee_device.get("model_id", "")
                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_POWER_SOURCE] = "Mains (single phase)"  # zigbee_device.get("power_source", "")
                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DESCRIPTION_USER] = ""  # zigbee_device.get("description", "")
                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DISABLED] = ""  # zigbee_device.get("disabled", "")
                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_SOFTWARE_BUILD_ID] = ""  # zigbee_device.get("software_build_id", "")

                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION] = dict()
                # zigbee_device_definition = zigbee_device['definition']

                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_DESCRIPTION_HW] = "Tuya Dimmer Module"  # zigbee_device_definition["description"]
                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_VENDOR] = "Tuya"  # zigbee_device_definition["vendor"]
                self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION][ZD_MODEL] = "TS0601_dimmer_3"  # zigbee_device_definition["model"]

                tuya_dimmer_properties = ["linkquality",
                                          "brightness_l1", "brightness_l2", "brightness_l3",
                                          "state_l1", "state_l2", "state_l3"]
                self.globals[ZD][zigbee_coordinator_ieee][tuya_dimmer_module_ieee][ZD_PROPERTIES] = tuya_dimmer_properties  # Store properties list in Globals for this zigbee device
                self.properties_set.add("linkquality")
                self.properties_set.add("brightness_l1")
                self.properties_set.add("brightness_l2")
                self.properties_set.add("brightness_l3")
                self.properties_set.add("state_l1")
                self.properties_set.add("state_l2")
                self.properties_set.add("state_l3")

            # TESTING Tuya Dimmer Module - ... END

            if self.globals[DEBUG]: self.zigbeeLogger.warning(f"All Properties: {sorted(self.properties_set)}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def handle_zigebee_coordinator_topic_groups(self, zc_dev_id, topics, topics_list, payload):
        try:
            zc_dev = indigo.devices[zc_dev_id]
            if not zc_dev.enabled:
                return

            json_payload = json.loads(payload)

            zigbee_coordinator_ieee = zc_dev.address
            if zigbee_coordinator_ieee not in self.globals[ZG]:
                if zigbee_coordinator_ieee[0:2] == "0x":
                    self.globals[ZG][zigbee_coordinator_ieee] = dict()
                else:
                    self.zigbeeLogger.warning(f"Groups has missing | invalid ieee recorded as '{zc_dev.name}' address: '{zigbee_coordinator_ieee}'")
                    return

            for zigbee_group in json_payload:

                if "friendly_name" in zigbee_group:
                    zigbee_friendly_name = zigbee_group["friendly_name"]
                    if zigbee_friendly_name not in self.globals[ZG][zigbee_coordinator_ieee]:
                        self.globals[ZG][zigbee_coordinator_ieee][zigbee_friendly_name] = dict()
                    self.globals[ZG][zigbee_coordinator_ieee][zigbee_friendly_name][ZG_ID] = zigbee_group["id"]
                    self.globals[ZG][zigbee_coordinator_ieee][zigbee_friendly_name][ZG_MEMBERS] = zigbee_group["members"]
                else:
                    continue

                if self.globals[DEBUG]: self.zigbeeLogger.warning(f"{topics} - GROUP: {zigbee_friendly_name}, ID: {self.globals[ZG][zigbee_coordinator_ieee][zigbee_friendly_name][ZG_ID]}")
                for zigbee_member in self.globals[ZG][zigbee_coordinator_ieee][zigbee_friendly_name][ZG_MEMBERS]:
                    #self.zigbeeLogger.warning(f"  ZIGBEE_MEMBER: {zigbee_member} [{type(zigbee_member)}]")
                    # for zigbee_member_detail in zigbee_members:
                    zigbee_endpoint = zigbee_member["endpoint"]
                    ieee_address = zigbee_member["ieee_address"]
                    if self.globals[DEBUG]: self.zigbeeLogger.warning(f"  ZIGBEE_MEMBER - ENDPOINT: {zigbee_endpoint}, IEEE_ADDRESS: {ieee_address}")
                    # self.zigbeeLogger.warning(f"  MEMBERS: {zigbee_member_detail} [{type(zigbee_member_detail)}]")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def handle_zigebee_group_topics(self, zc_dev_id, topics, topics_list, payload):
        try:
            group_friendly_name = topics_list[1]
            zc_dev = indigo.devices[zc_dev_id]
            zigbee_coordinator_ieee = zc_dev.address

            number_of_topics = len(topics_list)
            last_topic_index = number_of_topics - 1
            if topics_list[last_topic_index] in ("set", "get", "availability"):
                return

            if self.globals[DEBUG]: self.zigbeeLogger.warning(f"=========== > HANDLE ZIGBEE GROUP - TOPIC: {topics}, PAYLOAD: {payload}")

            zg_dev_id = self.globals[ZG][zigbee_coordinator_ieee][group_friendly_name].get(ZG_INDIGO_DEVICE_ID, 0)

            if zg_dev_id == 0 or zg_dev_id not in indigo.devices:
                return

            zg_dev = indigo.devices[zg_dev_id]

            if not zg_dev.enabled:
                return

            try:
                json_payload = json.loads(payload)
            except:
                self.zigbeeLogger.error(f"handle_zigebee_group_topics. Invalid JSON: Topic: {topics}, payload: {payload}")
                return

            self.key_value_lists = dict()
            self.key_value_lists[zg_dev_id] = list()

            if zg_dev.deviceTypeId == "zigbeeGroupRelay":
                self.process_property_state(zg_dev, json_payload)
            elif zg_dev.deviceTypeId == "zigbeeGroupDimmer":
                self.process_property_brightness(zg_dev, json_payload)
                self.process_property_color_mode(zg_dev, json_payload)
                self.process_property_color(zg_dev, json_payload)
                self.process_property_color_temp(zg_dev, json_payload)
                self.process_property_state(zg_dev, json_payload)

            # Now update the Indigo Zigbee device states for all devices in the device group
            for dev_id, key_value_list in self.key_value_lists.items():
                indigo.devices[dev_id].updateStatesOnServer(key_value_list)

            # if "state" in json_payload:
            #     on_off = True if json_payload["state"] == "ON" else False
            #     on_off_ui = json_payload["state"].lower()
            #     zg_dev_id = self.globals[ZG][zigbee_coordinator_ieee][group_friendly_name].get(ZG_INDIGO_DEVICE_ID, 0)
            #     # zg_dev_id = 32563519  # TOD: TEMP DEBUG TEST
            #     if  zg_dev_id != 0:
            #         zg_dev = indigo.devices[zg_dev_id]
            #         zg_dev.updateStateOnServer(key='onOffState', value=on_off, uiValue=on_off_ui)

            # json_payload["device"] = dict()
            # for zigbee_group_member in self.globals[ZG][zigbee_coordinator_ieee][group_friendly_name][ZG_MEMBERS]:
            #     zigbee_device_ieee = zigbee_group_member["ieee_address"]
            #     zigbee_device_friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME]
            #
            #     topic_out = f"{self.globals[ZC][zc_dev_id][MQTT_ROOT_TOPIC]}/{zigbee_device_friendly_name}"
            #
            #     json_payload["device"]["ieeeAddr"] = zigbee_device_ieee
            #     json_payload["device"]["friendlyName"] = zigbee_device_friendly_name
            #
            #     payload_out = json.dumps(json_payload)
            #     self.globals[ZC][zc_dev_id][MQTT_CLIENT].publish(topic_out, payload_out)
            #     self.zigbeeLogger.warning(f"                 ZIGBEE DEVICE - TOPIC: {topic_out}, PAYLOAD: {payload_out}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def handle_zigbee_device_topics(self, zc_dev_id, topics, topics_list, payload):
        try:
            zc_dev = indigo.devices[zc_dev_id]
            zigbee_coordinator_ieee = zc_dev.address

            # Following statement derives topic friendly name e.g. "Contact Sensor 1" or "study/contact sensor 1" etc
            topic_friendly_name = topics.replace(f"{self.globals[ZC][zc_dev_id][MQTT_ROOT_TOPIC]}/", "").replace("/set", "").replace("/get", "").replace("/availability", "")

            # if self.globals[DEBUG]: self.zigbeeLogger.warning(f"ZIGBEE_TOPIC_FRIENDLY_NAME: {topic_friendly_name}, ")
            if self.globals[DEBUG]: self.zigbeeLogger.warning(f"RECEIVED TOPIC: {topics}, PAYLOAD: {payload}")

            self.mqtt_filter_log_processing(zigbee_coordinator_ieee, topic_friendly_name, topics, payload)

            number_of_topics = len(topics_list)
            last_topic_index = number_of_topics - 1

            if topics_list[last_topic_index] == "availability":
                if payload == "offline":
                    # zc_dev.setErrorStateOnServer("offline")

                    # TODO: Update an internal state of Zigbee devices that are offline

                    self.zigbee_devices_offline[topic_friendly_name] = True

                    self.zigbeeLogger.warning(f"Availability for '{topic_friendly_name}' offline")
                else:
                    self.zigbee_devices_offline[topic_friendly_name] = False
                    zc_dev.setErrorStateOnServer(None)
                return
            elif topics_list[last_topic_index] in ["set", "get", "action"]:  # removes any topics ending in '/set' or '/get' or '/action'. Note: '/action' is added if Home Assistant Integration is enabled in Zigbee2mqtt settings
                return

            try:
                json_payload = json.loads(payload)
            except:
                if payload == "":
                    self.zigbeeLogger.error(f"handle_zigbee_device_topics. Invalid JSON: Topic: {topics}, payload is missing")
                else:
                    self.zigbeeLogger.error(f"handle_zigbee_device_topics. JSON payload missing: Topic: {topics}")
                return

            if "device" not in json_payload or "ieeeAddr" not in json_payload["device"]:
                if len(payload) > 0:
                    if not self.globals[MQTT_SUPPRESS_IEEE_MISSING]:
                        self.zigbeeLogger.error(f"MQTT topic '{topics}' is missing 'device' and|or 'ieeAddr' keys in JSON payload:\n")
                        self.zigbeeLogger.warning(f"    {payload}\n")
                        self.zigbeeLogger.error(f"    See Wiki Installation documentation at: https://github.com/autolog/Zigbee2mqtt_Bridge/wiki/Installation\n")
                else:
                    self.zigbeeLogger.error(f"MQTT topic '{topics}' is missing JSON payload. Payload is empty.")
                return
            zigbee_device_ieee = json_payload["device"]["ieeeAddr"]
            if zigbee_device_ieee not in self.globals[ZD][zigbee_coordinator_ieee]:
                if zigbee_device_ieee != zigbee_coordinator_ieee:
                    if self.globals[DEBUG]: self.zigbeeLogger.error(f"Zigbee Device with ieee '{zigbee_device_ieee}' is not joined to zigbee network - mqtt message ignored. Payload:\n{payload}")
                return

            zigbee_friendly_name = json_payload["device"]["friendlyName"]
            if topic_friendly_name != zigbee_friendly_name:
                self.zigbeeLogger.error(f"Zigbee Device Friendly Name '{zigbee_friendly_name}' differs from topic '{topic_friendly_name}'")
                self.zigbeeLogger.error(f"Zigbee JSON: Topic: {topics}, payload: {payload}")
                return

            # Check if linked to an Indigo device
            zd_dev_id = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID]

            if zd_dev_id == 0:  # Not linked to an Indigo device
                if self.globals[DEBUG]: self.zigbeeLogger.warning(f"Processing unlinked Zigbee device '{zigbee_friendly_name}' [{zigbee_device_ieee}]")
                return

            zd_dev = indigo.devices[zd_dev_id]

            offline = self.zigbee_devices_offline.get(topic_friendly_name, False)
            if offline:
                zd_dev.setErrorStateOnServer("offline")
                return

            if self.globals[DEBUG]: self.zigbeeLogger.error(f"Processing Zigbee device '{zigbee_friendly_name}' [{zigbee_device_ieee}]. Linked to Indigo device '{zd_dev.name}' [{zd_dev.deviceTypeId}]")

            self.iterate_grouped_devices(zd_dev.id)  # Initialise the key value lists for Indigo device updates for each device in the device group

            self.process_topic_last_seen(zd_dev, json_payload)  # For every Indigo Zigbee device type update 'last seen'

            self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] += 1
            match zd_dev.deviceTypeId:
                case "blind":
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_position(zd_dev, json_payload)
                    self.process_property_state(zd_dev, json_payload)
                    self.process_property_temperature(zd_dev, json_payload)

                case "button":
                    self.process_property_action(zd_dev, json_payload)
                    self.process_property_battery(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_voltage(zd_dev, json_payload)

                case "contactSensor":
                    self.process_property_battery(zd_dev, json_payload)
                    self.process_property_contact(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_voltage(zd_dev, json_payload)

                case "dimmer":
                    self.process_property_brightness(zd_dev, json_payload)
                    self.process_property_color_mode(zd_dev, json_payload)
                    self.process_property_color(zd_dev, json_payload)
                    self.process_property_color_temp(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_state(zd_dev, json_payload)

                case "humiditySensor":
                    self.process_property_battery(zd_dev, json_payload)
                    self.process_property_humidity(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_temperature(zd_dev, json_payload)
                    self.process_property_voltage(zd_dev, json_payload)

                case "illuminanceSensor":
                    # TODO: Work out how to handle illuminance when it is the primary device and not just an additional state
                    pass

                case "motionSensor":
                    self.process_property_battery(zd_dev, json_payload)
                    self.process_property_humidity(zd_dev, json_payload)
                    self.process_property_illuminance(zd_dev, json_payload)
                    self.process_property_occupancy(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_temperature(zd_dev, json_payload)
                    self.process_property_voltage(zd_dev, json_payload)

                case "multiDimmer":
                    self.process_property_multi_brightness(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_multi_state(zd_dev, json_payload)

                case "multiOutlet":
                    self.process_property_action(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_multi_state(zd_dev, json_payload)
                    self.process_property_voltage(zd_dev, json_payload)

                case "multiSensor":
                    self.process_property_battery(zd_dev, json_payload)
                    self.process_property_humidity(zd_dev, json_payload)
                    self.process_property_illuminance(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_occupancy(zd_dev, json_payload)
                    self.process_property_temperature(zd_dev, json_payload)
                    self.process_property_voltage(zd_dev, json_payload)

                case "multiSocket":
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_power_left_right(zigbee_coordinator_ieee, zd_dev, json_payload)
                    self.process_property_multi_state(zd_dev, json_payload)
                    self.process_property_temperature(zd_dev, json_payload)

                case "multiSwitch":
                    if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] > 1:
                        self.process_property_action_multi_switch(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_multi_state(zd_dev, json_payload)
                    self.process_property_temperature(zd_dev, json_payload)

                case "outlet":
                    self.process_property_energy(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_power(zigbee_coordinator_ieee, zd_dev, json_payload)
                    self.process_property_state(zd_dev, json_payload)
                    self.process_property_voltage(zd_dev, json_payload)

                case "presenceSensor":
                    pass

                case "radarSensor":
                    self.process_property_illuminance(zd_dev, json_payload)
                    self.process_property_radar(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_temperature(zd_dev, json_payload)

                case "remoteAudio":
                    # DEBUG self.zigbeeLogger.error(f"{zd_dev.name}: Message Count = {self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT]}")
                    if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] > 1:
                        self.process_property_action_remote_audio(zd_dev, json_payload)
                    self.process_property_battery(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)

                case "remoteDimmer":
                    # DEBUG self.zigbeeLogger.error(f"{zd_dev.name}: Message Count = {self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT]}")
                    if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] > 1:
                        self.process_property_action_remote_dimmer(zd_dev, json_payload)
                    self.process_property_battery(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)

                case "temperatureSensor":
                    self.process_property_battery(zd_dev, json_payload)
                    self.process_property_humidity(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_pressure(zd_dev, json_payload)
                    self.process_property_temperature(zd_dev, json_payload)
                    self.process_property_voltage(zd_dev, json_payload)

                case "sceneRotary":
                    self.process_property_battery(zd_dev, json_payload)
                    if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] > 1:
                        self.process_property_action_scene_rotary(zd_dev, json_payload, self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee])
                    self.process_property_rotations(zd_dev, json_payload, self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee])

                case "switch":
                    if self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] > 1:
                        self.process_property_action_switch(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_multi_state(zd_dev, json_payload)
                    self.process_property_temperature(zd_dev, json_payload)

                case "thermostat":
                    pass

                case "vibrationSensor":
                    self.process_property_battery(zd_dev, json_payload)
                    self.process_property_link_quality(zd_dev, json_payload)
                    self.process_property_action_vibration(zd_dev, json_payload)
                    self.process_property_angles(zd_dev, json_payload)
                    self.process_property_vibration(zd_dev, json_payload)
                    self.process_property_strength(zd_dev, json_payload)
                    self.process_property_voltage(zd_dev, json_payload)

            # Now update the Indigo Zigbee device states for all devices in the device group
            for dev_id, key_value_list in self.key_value_lists.items():
                dev = indigo.devices[dev_id]
                if dev.enabled:
                    dev.updateStatesOnServer(key_value_list)

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def iterate_grouped_devices(self, dev_id):
        # This method initialises the key value lists for Indigo device updates for each device in a device group
        try:
            self.key_value_lists = dict()
            dev_id_list = indigo.device.getGroupList(dev_id)
            for grouped_dev_id in dev_id_list:
                self.key_value_lists[grouped_dev_id] = list()

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_action(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "action" in json_payload:
                if zd_dev.pluginProps.get("uspAction", False):
                    action = json_payload["action"]
                    if action is None or action == "":
                        return
                    action_split = action.split("_")  # e.g. "1_single" or "double_left" or "button_1_single
                    if len(action_split) == 3 and action_split[0] == "button":
                        action_split_reformat = [action_split[1],action_split[2]]
                        action_split = action_split_reformat

                    if len(action_split) == 1:
                        button_number = 1
                        button_action = action_split[0]  # e.g. "single"
                    elif action_split[1] in ["left", "right", "both"]:
                        if action_split[1] == "left":
                            button_number = 1
                        elif action_split[1] == "right":
                            button_number = 2
                        else:
                            #Must be 'both'
                            button_number = 3
                        button_action = action_split[0]
                    else:
                        button_number = action_split[0]  # e.g. "1"
                        button_action = action_split[1]  # e.g. "single"
                    button_state_id = f"button_{button_number}"
                    number_of_buttons = int(zd_dev.pluginProps.get("uspNumberOfButtons", 1))
                    if int(button_number) <= number_of_buttons:
                        self.key_value_lists[zd_dev.id].append({'key': button_state_id, 'value': button_action})
                        if number_of_buttons == 1:
                            button_ui = "Button"
                            button_message_ui = "button"  # Note lowercase 'b' and trailing space!
                        else:
                            button_ui = f"Button {button_number}"
                            button_message_ui = f"button {button_number}"  # Note lowercase 'b' and trailing space!

                        self.key_value_lists[zd_dev.id].append({'key': 'lastButtonPressed', 'value': button_number, 'uiValue': button_ui})

                        # Kick off a one-second timer
                        try:
                            if zd_dev.id in self.timers:
                                self.timers[zd_dev.id].cancel()
                                del self.timers[zd_dev.id]
                        except Exception:
                            pass

                        self.timers[zd_dev.id] = threading.Timer(1.0, self.process_property_action_idle_timer, [[zd_dev.id, button_state_id]])
                        self.timers[zd_dev.id].start()

                        zd_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

                        if not bool(zd_dev.pluginProps.get("hideButtonBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" {button_message_ui} [{button_action}] action")

                    else:
                        self.zigbeeLogger.warning(f"received \"{zd_dev.name}\" unsupported button {button_number} [{button_action}] action")
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_action_vibration(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "action" in json_payload:
                if zd_dev.pluginProps.get("uspVibration", False):
                    vibration_action = json_payload["action"]
                    # zd_dev.updateStateOnServer(key="action", value="")  # To force Indigo to recognise a state change

                    if vibration_action != zd_dev.states["action"]:
                        self.key_value_lists[zd_dev.id].append({'key': "action", 'value': vibration_action})
                        if not bool(zd_dev.pluginProps.get("hideVibrationBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" vibration sensor '{vibration_action}' event")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_action_remote_audio(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "action" in json_payload:
                if zd_dev.pluginProps.get("uspRemoteAudio", False):
                    remote_action = json_payload["action"]
                    zd_dev.updateStateOnServer(key="action", value="")  # To force Indigo to recognise a state change

                    self.key_value_lists[zd_dev.id].append({'key': "action", 'value': remote_action})
                    self.key_value_lists[zd_dev.id].append({'key': 'lastButtonPressed', 'value': remote_action, 'uiValue': remote_action})

                    # Kick off a one-second timer
                    try:
                        if zd_dev.id in self.timers:
                            self.timers[zd_dev.id].cancel()
                            del self.timers[zd_dev.id]
                    except Exception:
                        pass

                    self.timers[zd_dev.id] = threading.Timer(1.0, self.process_property_action_idle_timer, [[zd_dev.id, "action"]])
                    self.timers[zd_dev.id].start()

                    zd_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

                    if not bool(zd_dev.pluginProps.get("hideRemoteAudioBroadcast", False)):
                        self.zigbeeLogger.info(f"received \"{zd_dev.name}\" {remote_action} action")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_action_remote_dimmer(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "action" in json_payload:
                if zd_dev.pluginProps.get("uspRemoteDimmer", False):
                    remote_action = json_payload["action"]
                    zd_dev.updateStateOnServer(key="action", value="")  # To force Indigo to recognise a state change

                    self.key_value_lists[zd_dev.id].append({'key': "action", 'value': remote_action})
                    self.key_value_lists[zd_dev.id].append({'key': 'lastButtonPressed', 'value': remote_action, 'uiValue': remote_action})

                    # Kick off a one-second timer
                    try:
                        if zd_dev.id in self.timers:
                            self.timers[zd_dev.id].cancel()
                            del self.timers[zd_dev.id]
                    except Exception:
                        pass

                    self.timers[zd_dev.id] = threading.Timer(1.0, self.process_property_action_idle_timer, [[zd_dev.id, "action"]])
                    self.timers[zd_dev.id].start()

                    zd_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

                    if not bool(zd_dev.pluginProps.get("hideRemoteDimmerBroadcast", False)):
                        self.zigbeeLogger.info(f"received \"{zd_dev.name}\" '{remote_action}' action")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_action_scene_rotary(self, zd_dev, json_payload, zd_dev_internal):
        try:
            if not zd_dev.enabled:
                return
            if "action" in json_payload:
                if zd_dev.pluginProps.get("uspSceneRotary", False):
                    rotary_action = json_payload["action"]
                    zd_dev.updateStateOnServer(key="action", value="")  # To force Indigo to recognise a state change

                    self.key_value_lists[zd_dev.id].append({'key': "action", 'value': rotary_action})
                    self.key_value_lists[zd_dev.id].append({'key': 'lastAction', 'value': rotary_action, 'uiValue': rotary_action})

                    if rotary_action == "start_rotating":
                        rotation_variable_id = int(zd_dev.pluginProps.get("uspRotationVariableId", 0))
                        if rotation_variable_id != 0:
                            try:
                                rotation_variable = int(indigo.variables[rotation_variable_id].value)
                            except Exception as exception_error:
                                rotation_variable = 0
                            if rotation_variable < 0:
                                rotation_variable = 0
                            elif rotation_variable > 100:
                                rotation_variable = 100
                            zd_dev_internal[ZD_ROTATION_VARIABLE] = rotation_variable
                            zd_dev_internal[ZD_ROTATION_INITIAL] = rotation_variable

                    # Kick off a one-second timer
                    try:
                        if zd_dev.id in self.timers:
                            self.timers[zd_dev.id].cancel()
                            del self.timers[zd_dev.id]
                    except Exception:
                        pass

                    self.timers[zd_dev.id] = threading.Timer(1.0, self.process_property_action_idle_timer, [[zd_dev.id, "action"]])
                    self.timers[zd_dev.id].start()

                    zd_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

                    if not bool(zd_dev.pluginProps.get("hideSceneRotaryBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" rotary knob '{rotary_action}' event")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_action_multi_switch(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "action" in json_payload:
                if zd_dev.pluginProps.get("uspMultiSwitchAction", False):
                    multi_switch_action = json_payload["action"]
                    zd_dev.updateStateOnServer(key="action", value="")  # To force Indigo to recognise a state change

                    self.key_value_lists[zd_dev.id].append({'key': "action", 'value': multi_switch_action})
                    self.key_value_lists[zd_dev.id].append({'key': 'lastAction', 'value': multi_switch_action, 'uiValue': multi_switch_action})

                    # Kick off a one-second timer
                    try:
                        if zd_dev.id in self.timers:
                            self.timers[zd_dev.id].cancel()
                            del self.timers[zd_dev.id]
                    except Exception:
                        pass

                    self.timers[zd_dev.id] = threading.Timer(1.0, self.process_property_action_idle_timer, [[zd_dev.id, "action"]])
                    self.timers[zd_dev.id].start()

                    zd_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

                    if not bool(zd_dev.pluginProps.get("hideMultiSwitchActionBroadcast", False)):
                        self.zigbeeLogger.info(f"received \"{zd_dev.name}\" multi-switch '{multi_switch_action}' event")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_action_switch(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "action" in json_payload:
                if zd_dev.pluginProps.get("uspSwitchAction", False):
                    multi_switch_action = json_payload["action"]
                    zd_dev.updateStateOnServer(key="action", value="")  # To force Indigo to recognise a state change

                    self.key_value_lists[zd_dev.id].append({'key': "action", 'value': multi_switch_action})
                    self.key_value_lists[zd_dev.id].append({'key': 'lastAction', 'value': multi_switch_action, 'uiValue': multi_switch_action})

                    # Kick off a one-second timer
                    try:
                        if zd_dev.id in self.timers:
                            self.timers[zd_dev.id].cancel()
                            del self.timers[zd_dev.id]
                    except Exception:
                        pass

                    self.timers[zd_dev.id] = threading.Timer(1.0, self.process_property_action_idle_timer, [[zd_dev.id, "action"]])
                    self.timers[zd_dev.id].start()

                    zd_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

                    if not bool(zd_dev.pluginProps.get("hideSwitchActionBroadcast", False)):
                        self.zigbeeLogger.info(f"received \"{zd_dev.name}\" switch '{multi_switch_action}' event")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_action_idle_timer(self, parameters):
        try:
            zd_dev_id = parameters[0]
            zd_dev = indigo.devices[zd_dev_id]

            # self.zigbeeLogger.warning(f"Timer for {zd_dev.name} [{zd_dev.address}] invoked for set_idle")
            try:
                if zd_dev_id in self.timers:
                    self.timers[zd_dev.id].cancel()
                del self.timers[zd_dev.id]
            except Exception:
                pass

            button_state_id = parameters[1]
            zd_dev.updateStateOnServer(button_state_id, "idle")
            zd_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

            # TODO: Kick off timer to change state to "idle" + set UI image

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_angles(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if zd_dev.pluginProps.get("uspAngles", False):
                angles_broadcast_ui = ""

                angle = json_payload.get("angle", None)
                try:
                    zd_dev_state_angle = int(zd_dev.states["angle"])
                except ValueError:
                    zd_dev_state_angle = 0
                if angle is not None and int(angle) != zd_dev_state_angle:
                    self.key_value_lists[zd_dev.id].append({'key': "angle", 'value': angle})
                    angles_broadcast_ui = f"{angles_broadcast_ui} Angle: {angle},"

                angle_x = json_payload.get("angle_x", None)
                try:
                    zd_dev_state_angle_x = int(zd_dev.states["angle_x"])
                except ValueError:
                    zd_dev_state_angle_x = 0
                if angle_x is not None and int(angle_x) != zd_dev_state_angle_x:
                    self.key_value_lists[zd_dev.id].append({'key': "angle_x", 'value': angle_x})
                    angles_broadcast_ui = f"{angles_broadcast_ui} Angle_X: {angle_x},"

                angle_x_absolute = json_payload.get("angle_x_absolute", None)
                try:
                    zd_dev_state_angle_x_absolute = int(zd_dev.states["angle_x_absolute"])
                except ValueError:
                    zd_dev_state_angle_x_absolute = 0
                if angle_x_absolute is not None and int(angle_x_absolute) != zd_dev_state_angle_x_absolute:
                    self.key_value_lists[zd_dev.id].append({'key': "angle_x_absolute", 'value': angle_x_absolute})
                    angles_broadcast_ui = f"{angles_broadcast_ui} Angle_X_Absolute: {angle_x_absolute},"

                angle_y = json_payload.get("angle_y", None)
                try:
                    zd_dev_state_angle_y = int(zd_dev.states["angle_y"])
                except ValueError:
                    zd_dev_state_angle_y = 0
                if angle_y is not None and int(angle_y) != zd_dev_state_angle_y:
                    self.key_value_lists[zd_dev.id].append({'key': "angle_y", 'value': angle_y})
                    angles_broadcast_ui = f"{angles_broadcast_ui} Angle_Y: {angle_y},"

                angle_y_absolute = json_payload.get("angle_y_absolute", None)
                try:
                    zd_dev_state_angle_y_absolute = int(zd_dev.states["angle_y_absolute"])
                except ValueError:
                    zd_dev_state_angle_y_absolute = 0
                if angle_y_absolute is not None and int(angle_y_absolute) != zd_dev_state_angle_y_absolute:
                    self.key_value_lists[zd_dev.id].append({'key': "angle_y_absolute", 'value': angle_y_absolute})
                    angles_broadcast_ui = f"{angles_broadcast_ui} Angle_Y_Absolute: {angle_y_absolute},"

                angle_z = json_payload.get("angle_z", None)
                try:
                    zd_dev_state_angle_z = int(zd_dev.states["angle_z"])
                except ValueError:
                    zd_dev_state_angle_z = 0
                if angle_z is not None and int(angle_z) != zd_dev_state_angle_z:
                    self.key_value_lists[zd_dev.id].append({'key': "angle_z", 'value': angle_z})
                    angles_broadcast_ui = f"{angles_broadcast_ui} Angle_Z: {angle_z},"

                if not bool(zd_dev.pluginProps.get("hideAnglesBroadcast", False)):
                    if len(angles_broadcast_ui) > 0:
                        if angles_broadcast_ui[-1] == ",":
                            angles_broadcast_ui = angles_broadcast_ui[:-1]
                        self.zigbeeLogger.info(f"received \"{zd_dev.name}\"{angles_broadcast_ui}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_rotations(self, zd_dev, json_payload, zd_dev_internal):
        try:
            if not zd_dev.enabled:
                return
            if zd_dev.pluginProps.get("uspRotations", False):
                rotations_broadcast_ui = ""

                try:
                    zd_dev_state_rotation_angle = int(zd_dev.states["rotation_angle"])
                except ValueError:
                    zd_dev_state_rotation_angle = 0
                action_rotation_angle = json_payload.get("action_rotation_angle", None)
                if action_rotation_angle is not None:
                    try:
                        action_rotation_angle = int(action_rotation_angle)
                        if action_rotation_angle != zd_dev_state_rotation_angle:
                            self.key_value_lists[zd_dev.id].append({'key': "rotation_angle", 'value': action_rotation_angle})
                            rotations_broadcast_ui = f"{rotations_broadcast_ui} Rotation Angle: {action_rotation_angle},"

                        rotation_variable_id = int(zd_dev.pluginProps.get("uspRotationVariableId", 0))
                        if rotation_variable_id != 0:
                            try:
                                rotation_factor = int(zd_dev.pluginProps.get("uspRotationVariableFactor", 1))
                            except ValueError as exception_error:
                                rotation_factor = 1

                            try:
                                rotation_variable = int(indigo.variables[rotation_variable_id].value)
                            except ValueError as exception_error:
                                rotation_variable = 0
                            if rotation_variable < 0:
                                rotation_variable = 0
                            elif rotation_variable > 100:
                                rotation_variable = 100

                            action_rotation_change = int(action_rotation_angle / 12)  # action_rotation_angle is multiple of 12
                            action_rotation_change = action_rotation_change * rotation_factor
                            try:
                                action_rotation_new_value = zd_dev_internal[ZD_ROTATION_INITIAL] + action_rotation_change
                                if action_rotation_new_value < 0:
                                    action_rotation_new_value = 0
                                elif action_rotation_new_value > 100:
                                    action_rotation_new_value = 100
                                indigo.variable.updateValue(rotation_variable_id, value=f"{action_rotation_new_value}")
                            except KeyError as exception_error:
                                pass

                    except ValueError as exception_error:
                        pass

                try:
                    zd_dev_state_rotation_angle_speed = int(zd_dev.states["rotation_angle_speed"])
                except ValueError:
                    zd_dev_state_rotation_angle_speed = 0
                action_rotation_angle_speed = json_payload.get("action_rotation_angle_speed", None)
                if action_rotation_angle_speed is not None:
                    try:
                        action_rotation_angle_speed = int(action_rotation_angle_speed)
                        if action_rotation_angle_speed != zd_dev_state_rotation_angle_speed:
                            self.key_value_lists[zd_dev.id].append({'key': "rotation_angle_speed", 'value': action_rotation_angle_speed})
                            rotations_broadcast_ui = f"{rotations_broadcast_ui} Rotation Angle Speed: {action_rotation_angle_speed},"
                    except ValueError as exception_error:
                        pass

                try:
                    zd_dev_state_rotation_percent = int(zd_dev.states["rotation_percent"])
                except ValueError:
                    zd_dev_state_rotation_percent = 0
                action_rotation_percent = json_payload.get("action_rotation_percent", None)
                if action_rotation_percent is not None:
                    try:
                        action_rotation_percent = int(action_rotation_percent)
                        if action_rotation_percent != zd_dev_state_rotation_percent:
                            self.key_value_lists[zd_dev.id].append({'key': "rotation_percent", 'value': action_rotation_percent})
                            rotations_broadcast_ui = f"{rotations_broadcast_ui} Rotation Percent: {action_rotation_percent},"
                    except ValueError as exception_error:
                        pass

                try:
                    zd_dev_state_rotation_percent_positive = int(zd_dev.states["rotation_percent_positive"])
                except ValueError:
                    zd_dev_state_rotation_percent_positive = 0
                action_rotation_percent_positive = json_payload.get("action_rotation_percent", None)
                if action_rotation_percent_positive is not None:
                    try:
                        action_rotation_percent_positive = int(action_rotation_percent_positive)
                        if action_rotation_percent_positive < 0:
                            action_rotation_percent_positive = 0
                        if action_rotation_percent_positive != zd_dev_state_rotation_percent_positive:
                            self.key_value_lists[zd_dev.id].append({'key': "rotation_percent_positive", 'value': action_rotation_percent_positive})
                            if action_rotation_percent != action_rotation_percent_positive:
                                # Only show 'Rotation Positive Percent' value if not the same as 'Rotation Percent' i.e 'Rotation Percent' is negative.
                                rotations_broadcast_ui = f"{rotations_broadcast_ui} Rotation Positive Percent: {action_rotation_percent_positive},"
                    except ValueError as exception_error:
                        pass

                try:
                    zd_dev_state_rotation_percent_speed = int(zd_dev.states["rotation_percent_speed"])
                except ValueError:
                    zd_dev_state_rotation_percent_speed = 0
                action_rotation_percent_speed = json_payload.get("action_rotation_percent_speed", None)
                if action_rotation_percent_speed is not None:
                    try:
                        action_rotation_percent_speed = int(action_rotation_percent_speed)
                        if action_rotation_percent_speed != zd_dev_state_rotation_percent_speed:
                            self.key_value_lists[zd_dev.id].append({'key': "rotation_percent_speed", 'value': action_rotation_percent_speed})
                            rotations_broadcast_ui = f"{rotations_broadcast_ui} Rotation Percent Speed: {action_rotation_percent_speed},"
                    except ValueError as exception_error:
                        pass

                try:
                    zd_dev_state_rotation_time = int(zd_dev.states["rotation_time"])
                except ValueError:
                    zd_dev_state_rotation_time = 0
                action_rotation_time = json_payload.get("action_rotation_time", None)
                if action_rotation_time is not None:
                    try:
                        action_rotation_time = int(action_rotation_time)
                        if action_rotation_time != zd_dev_state_rotation_time:
                            self.key_value_lists[zd_dev.id].append({'key': "rotation_time", 'value': action_rotation_time})
                            rotations_broadcast_ui = f"{rotations_broadcast_ui} Rotation Time: {action_rotation_time},"
                    except ValueError as exception_error:
                        pass

                if not bool(zd_dev.pluginProps.get("hideRotationsBroadcast", False)):
                    if len(rotations_broadcast_ui) > 0:
                        if rotations_broadcast_ui[-1] == ",":  # Check for and remove trailing comma
                            rotations_broadcast_ui = rotations_broadcast_ui[:-1]
                        self.zigbeeLogger.info(f"received \"{zd_dev.name}\"{rotations_broadcast_ui}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_battery(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "battery" in json_payload:
                if zd_dev.pluginProps.get("SupportsBatteryLevel", False):
                    valid = False
                    try:
                        battery_level = int(json_payload["battery"])
                        valid = True
                    except TypeError:
                        pass
                    except ValueError:
                        try:
                            battery_level = int(float(json_payload["battery"]))
                            valid = True
                        except ValueError:
                            self.zigbeeLogger.warning(
                                f"received battery level event with an invalid payload of \"{json_payload['battery']}\" for device \"{zd_dev.name}\". Event discarded and ignored.")
                    if valid:
                        if zd_dev.states["batteryLevel"] != battery_level:  # noqa: reference before assignment
                            self.key_value_lists[zd_dev.id].append({'key': 'batteryLevel', 'value': battery_level})
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" battery level {battery_level}%")
                        else:
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged battery level: {battery_level}%")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_brightness(self, zd_dev, json_payload):
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
                    self.zigbeeLogger.info(f"received brightness event with an invalid payload of \"{json_payload['brightness']}\" for device \"{zd_dev.name}\". Event discarded and ignored.")
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
                        self.zigbeeLogger.error(f"received \"{zd_dev.name}\" status update of \"{brightness_100_ui}\" for missing brightnessLevel state.")  # noqa: reference before assignment

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_color(self, zd_dev, json_payload):
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
                        payload = json.dumps(json_payload)
                        self.zigbeeLogger.info(f"received color event with an unknown payload of \"{payload}\" for device \"{zd_dev.name}\". Event discarded and ignored.")
                except ValueError:
                    payload = json.dumps(json_payload)
                    self.zigbeeLogger.info(f"received color event with an invalid payload of \"{payload}\" for device \"{zd_dev.name}\". Event discarded and ignored.")
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

    def process_property_color_mode(self, zd_dev, json_payload):
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
                except:
                    payload = json.dumps(json_payload)
                    self.zigbeeLogger.info(f"received color mode with an invalid payload of \"{payload}\" for device \"{zd_dev.name}\". Event discarded and ignored.")
                if valid:
                    self.key_value_lists[zd_dev.id].append({"key": "colorMode", "value": derived_color_mode})  # noqa: reference before assignment

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_color_temp(self, zd_dev, json_payload):
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
                    self.zigbeeLogger.info(f"received color event with an invalid payload of \"{json_payload['brightness']}\" for device \"{zd_dev.name}\". Event discarded and ignored.")
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

    def process_property_contact(self, zd_dev, json_payload):
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

    def process_property_energy(self, zd_dev, json_payload):
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
                        decimal_places = int(zd_dev.pluginProps.get("uspEnergyDecimalPlaces", 0))
                        value, uiValue = self.processDecimalPlaces(energy, decimal_places, energy_units_ui, INDIGO_NO_SPACE_BEFORE_UNITS)
                        if zd_dev.states["accumEnergyTotal"] != value:  # noqa: reference before assignment
                            self.key_value_lists[zd_dev.id].append({'key': 'accumEnergyTotal', 'value': value, 'uiValue': uiValue})
                            if not bool(zd_dev.pluginProps.get("hideEnergyBroadcast", False)):
                                self.zigbeeLogger.info(f"received \"{zd_dev.name}\" accumulated energy total update to {uiValue}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_humidity(self, zd_dev, json_payload):
        try:
            if not zd_dev.pluginProps.get("uspHumidity", False) or not "humidity" in json_payload:
                return

            uspHumidityIndigo = zd_dev.pluginProps.get("uspHumidityIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE)
            zd_dev_to_process = zd_dev
            update_secondary_device = False
            state_to_update = "humidity"  # Primary device
            secondary_dev_id = zd_dev.pluginProps.get("secondaryDeviceHumiditySensor", 0)  # Returns int zero if no secondary humidity device
            if uspHumidityIndigo == INDIGO_SECONDARY_DEVICE and secondary_dev_id != 0:  # noqa: Duplicate code
                if secondary_dev_id in indigo.devices:
                    zd_dev_to_process = indigo.devices[secondary_dev_id]
                    update_secondary_device = True
                    state_to_update = "sensorValue"  # Secondary device

            if not zd_dev_to_process.enabled:
                return

            if uspHumidityIndigo == INDIGO_SECONDARY_DEVICE and not update_secondary_device:
                self.zigbeeLogger.warning(f"received humidity event with a raw payload of \"{json_payload['humidity']}\" for a missing secondary device associated with device \"{zd_dev_to_process.name}\". Event discarded and ignored.")
                return

            # At this point we have a primary device 'zd_dev' and a 'zd_dev_to_process' device which can either be the primary devoice or a secondary device.
            # The "humidityInput1" (primary) or "sensorValue" (secondary) state will be updated on the 'zd_dev_to_process' device if valid and has a changed value

            try:
                humidity = float(json_payload["humidity"])
                valid = True
            except ValueError:
                self.zigbeeLogger.warning(f"received humidity event with an invalid payload of \"{json_payload['humidity']}\" for device \"{zd_dev_to_process.name}\". Event discarded and ignored.")
                valid = False

            if valid:
                decimal_places = int(zd_dev.pluginProps.get("uspHumidityDecimalPlaces", 0))
                humidity_value, ui_humidity_value = self.processDecimalPlaces(humidity, decimal_places, "%", INDIGO_ONE_SPACE_BEFORE_UNITS)  # noqa: reference before assignment
                if state_to_update in zd_dev_to_process.states:
                    if zd_dev_to_process.states[state_to_update] != humidity:  # noqa: Reference bdeore assignment
                        if state_to_update == "sensorValue":
                            zd_dev_to_process.updateStateImageOnServer(indigo.kStateImageSel.HumiditySensor)
                        self.key_value_lists[zd_dev_to_process.id].append({'key': state_to_update, 'value': humidity_value, 'uiValue': ui_humidity_value})
                        if not bool(zd_dev.pluginProps.get("hideHumidityBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" humidity level {ui_humidity_value}")
                    else:
                        if not bool(zd_dev.pluginProps.get("hideHumidityBroadcast", False)):
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" unchanged humidity level {ui_humidity_value}")
                else:
                    self.zigbeeLogger.error(f"received \"{zd_dev_to_process.name}\" status update of \"{ui_humidity_value}\" for missing humidity state.")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_illuminance(self, zd_dev, json_payload):
        try:
            if not zd_dev.pluginProps.get("uspIlluminance", False):
                return

            if not "illuminance" in json_payload and not "illuminance_lux" in json_payload:
                return

            uspIlluminanceIndigo = zd_dev.pluginProps.get("uspIlluminanceIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE)
            zd_dev_to_process = zd_dev
            update_secondary_device = False
            state_to_update = "illuminance"  # Primary device
            secondary_dev_id = zd_dev.pluginProps.get("secondaryDeviceIlluminanceSensor", 0)  # Returns int zero if no secondary illuminance device
            if uspIlluminanceIndigo == INDIGO_SECONDARY_DEVICE and secondary_dev_id != 0:  # noqa: Duplicate code
                if secondary_dev_id in indigo.devices:
                    zd_dev_to_process = indigo.devices[secondary_dev_id]
                    update_secondary_device = True
                    state_to_update = "sensorValue"  # Secondary device

            if not zd_dev_to_process.enabled:
                return

            if "illuminance_lux" in json_payload:
                illuminance = json_payload["illuminance_lux"]
            else:
                illuminance = json_payload["illuminance"]

            if uspIlluminanceIndigo == INDIGO_SECONDARY_DEVICE and not update_secondary_device:
                self.zigbeeLogger.warning(f"received illuminance event with a raw payload of \"{illuminance}\" for a missing secondary device associated with device \"{zd_dev_to_process.name}\". Event discarded and ignored.")
                return

            # At this point we have a primary device 'zd_dev' and a 'zd_dev_to_process' device which can either be the primary devoice or a secondary device.
            # The "illuminance" (primary) or "sensorValue" (secondary) state will be updated on the 'zd_dev_to_process' device if valid and has a changed value

            try:
                if "illuminance_lux" in json_payload:
                    illuminance = float(json_payload["illuminance_lux"])
                else:
                    illuminance = float(json_payload["illuminance"])
                valid = True
            except ValueError:
                self.zigbeeLogger.warning(f"received illuminance event with an invalid payload of \"{json_payload}\" for device \"{zd_dev_to_process.name}\". Event discarded and ignored.")
                valid = False

            if valid:
                decimal_places = int(zd_dev.pluginProps.get("uspIlluminanceDecimalPlaces", 0))
                illuminance_units_ui = zd_dev.pluginProps.get("uspIlluminanceUnits", "")
                illuminance_value, ui_illuminance_value = self.processDecimalPlaces(illuminance, decimal_places, illuminance_units_ui, INDIGO_ONE_SPACE_BEFORE_UNITS)  # noqa: reference before assignment
                if state_to_update in zd_dev_to_process.states:
                    if zd_dev_to_process.states[state_to_update] != illuminance:  # noqa: Reference bdeore assignment
                        if state_to_update == "sensorValue":
                            zd_dev_to_process.updateStateImageOnServer(indigo.kStateImageSel.LightSensor)
                        self.key_value_lists[zd_dev_to_process.id].append({'key': state_to_update, 'value': illuminance_value, 'uiValue': ui_illuminance_value})
                        if not bool(zd_dev.pluginProps.get("hideIlluminanceBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" illuminance {ui_illuminance_value}")
                    else:
                        if not bool(zd_dev.pluginProps.get("hideIlluminanceBroadcast", False)):
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" unchanged illuminance {ui_illuminance_value}")
                else:
                    self.zigbeeLogger.error(f"received \"{zd_dev_to_process.name}\" status update of \"{ui_illuminance_value}\" for missing illuminance state.")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_topic_last_seen(self, zd_dev, json_payload):
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
                    self.zigbeeLogger.info(f"received last_seen event with an invalid payload of \"{json_payload['last_seen']}\" for device \"{zd_dev.name}\". Event discarded and ignored.")
                if valid:
                    if "last_seen" in zd_dev.states:
                        if zd_dev.states["last_seen"] != last_seen:  # noqa: reference before assignment
                            self.key_value_lists[zd_dev.id].append({'key': 'last_seen', 'value': last_seen})
                            # self.key_value_lists[zd_dev.id].append({'key': 'id', 'value': last_seen})  #TODO: Remove - SQL Logger Test
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" last seen {last_seen}")
                        else:
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged last seen {last_seen}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_link_quality(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "linkquality" in json_payload:
                if zd_dev.pluginProps.get("uspLinkQuality", False):
                    linkquality = json_payload["linkquality"]
                    self.key_value_lists[zd_dev.id].append({'key': 'linkQuality', 'value': linkquality})
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_multi_state(self, zd_dev, json_payload):
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
            def process_secondary_switches(device_type, switch):
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
                    # TODO: Check for zero
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
            def process_secondary_dimmers(device_type, dimmer):
                try:
                    if device_type == "multiDimmer":
                        secondary_device_id_property_key = f"secondaryDeviceMultiDimmer{dimmer}"
                    else:
                        return
                    secondary_dev_id = zd_dev.pluginProps.get(secondary_device_id_property_key, 0)
                    # TODO: Check for zero
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
                            self.zigbeeLogger.info(f"received brightness event with an invalid payload of \"{json_payload['brightness']}\" for device \"{secondary_dev.name}\". Event discarded and ignored.")
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
                                self.zigbeeLogger.error(f"received \"{secondary_dev.name}\" status update of \"{brightness_100_ui}\" for missing brightnessLevel state.")  # noqa: reference before assignment

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

    def process_property_occupancy(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "occupancy" in json_payload:
                if zd_dev.pluginProps.get("uspOccupancy", False):
                    # on_off_state = False if json_payload["occupancy"] == True else True  # TODO: Is this needed?
                    on_off_state_ui = "on" if json_payload["occupancy"] == True else "off"
                    on_off_state = json_payload["occupancy"]
                    if zd_dev.states["onOffState"] != on_off_state:
                        self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                        if not bool(zd_dev.pluginProps.get("hideMotionBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" motion sensor '{on_off_state_ui}' event")
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_position(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "position" in json_payload:
                valid = False
                try:
                    position = int(json_payload["position"])
                    valid = True
                except ValueError:
                    self.zigbeeLogger.info(f"received position event with an invalid payload of \"{json_payload['position']}\" for device \"{zd_dev.name}\". Event discarded and ignored.")
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
                        self.zigbeeLogger.error(f"received \"{zd_dev.name}\" position update of \"{position}\" for missing brightnessLevel state.")  # noqa: reference before assignment

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_power(self, zigbee_coordinator_ieee, zd_dev, json_payload):
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
                    minimumPowerLevel = float(zd_dev.pluginProps.get("uspPowerMinimumReportingLevel", 0.0))
                    reportingPowerHysteresis = float(zd_dev.pluginProps.get("uspPowerReportingHysteresis", 6.0))
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

                    decimal_places = int(zd_dev.pluginProps.get("uspPowerDecimalPlaces", 0))
                    value, uiValue = self.processDecimalPlaces(power, decimal_places, power_units_ui, INDIGO_NO_SPACE_BEFORE_UNITS)
                    self.key_value_lists[zd_dev.id].append({'key': 'curEnergyLevel', 'value': value, 'uiValue': uiValue})
                    if report_power_state:
                        if not bool(zd_dev.pluginProps.get("hidePowerBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" power update to {uiValue}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_power_left_right(self, zigbee_coordinator_ieee, zd_dev, json_payload):
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
                    minimumPowerLevel = float(zd_dev.pluginProps.get(f"uspPower{side}MinimumReportingLevel", 0.0))
                    reportingPowerHysteresis = float(zd_dev.pluginProps.get(f"uspPower{side}ReportingHysteresis", 6.0))
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

                    decimal_places = int(zd_dev.pluginProps.get(f"uspPower{side}DecimalPlaces", 0))
                    value, uiValue = self.processDecimalPlaces(power, decimal_places, power_units_ui, INDIGO_NO_SPACE_BEFORE_UNITS)
                    self.key_value_lists[zd_dev_to_process.id].append({'key': 'curEnergyLevel', 'value': value, 'uiValue': uiValue})
                    if report_power_state:
                        if not bool(zd_dev.pluginProps.get(f"hidePower{side}Broadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" power update to {uiValue}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_pressure(self, zd_dev, json_payload):
        try:
            if not zd_dev.pluginProps.get("uspPressure", False) or not "pressure" in json_payload:
                return

            uspPressureIndigo = zd_dev.pluginProps.get("uspPressureIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE)
            zd_dev_to_process = zd_dev
            update_secondary_device = False
            state_to_update = "pressure"  # Primary device
            secondary_dev_id = zd_dev.pluginProps.get("secondaryDevicePressureSensor", 0)  # Returns int zero if no secondary pressure device
            if uspPressureIndigo == INDIGO_SECONDARY_DEVICE and secondary_dev_id != 0:  # noqa: Duplicate code
                if secondary_dev_id in indigo.devices:
                    zd_dev_to_process = indigo.devices[secondary_dev_id]
                    update_secondary_device = True
                    state_to_update = "sensorValue"  # Secondary device
            if not zd_dev_to_process.enabled:
                return
            if uspPressureIndigo == INDIGO_SECONDARY_DEVICE and not update_secondary_device:
                self.zigbeeLogger.warning(f"received pressure event with a raw payload of \"{json_payload['pressure']}\" for a missing secondary device associated with device \"{zd_dev_to_process.name}\". Event discarded and ignored.")
                return

            # At this point we have a primary device 'zd_dev' and a 'zd_dev_to_process' device which can either be the primary devoice or a secondary device.
            # The "pressure" (primary) or "sensorValue" (secondary) state will be updated on the 'zd_dev_to_process' device if valid and has a changed value

            try:
                pressure = float(json_payload["pressure"])
                valid = True
            except ValueError:
                self.zigbeeLogger.warning(f"received pressure event with an invalid payload of \"{json_payload['pressure']}\" for device \"{zd_dev_to_process.name}\". Event discarded and ignored.")
                valid = False

            if valid:
                decimal_places = int(zd_dev.pluginProps.get("uspPressureDecimalPlaces", 0))
                pressure_units_ui = zd_dev.pluginProps.get("uspPressureUnits", "")
                pressure_value, ui_pressure_value = self.processDecimalPlaces(pressure, decimal_places, pressure_units_ui, INDIGO_ONE_SPACE_BEFORE_UNITS)  # noqa: reference before assignment
                if state_to_update in zd_dev_to_process.states:
                    if zd_dev_to_process.states[state_to_update] != pressure_value:  # noqa: Reference before assignment
                        self.key_value_lists[zd_dev_to_process.id].append({'key': state_to_update, 'value': pressure_value, 'uiValue': ui_pressure_value})
                        if not bool(zd_dev.pluginProps.get("hidePressureBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" pressure level {ui_pressure_value}")
                    else:
                        if not bool(zd_dev.pluginProps.get("hidePressureBroadcast", False)):
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" unchanged pressure level {ui_pressure_value}")
                else:
                    self.zigbeeLogger.error(f"received \"{zd_dev_to_process.name}\" status update of \"{ui_pressure_value}\" for missing pressure state.")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_radar(self, zd_dev, json_payload):
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

            # Check for Radar [Presence & Presence Event] e.g. Aqara FP1
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

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_state(self, zd_dev, json_payload):
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

    def process_property_strength(self, zd_dev, json_payload):
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

    def process_property_tamper(self, zd_dev, json_payload):
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

    def process_property_temperature(self, zd_dev, json_payload):
        try:
            if not zd_dev.pluginProps.get("uspTemperature", False):
                return
            if not "temperature" in json_payload and not "device_temperature" in json_payload:
                return

            uspTemperatureIndigo = zd_dev.pluginProps.get("uspTemperatureIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE)
            zd_dev_to_process = zd_dev
            update_secondary_device = False
            state_to_update = "sensorValue"  # Primary device - Main UI State
            if uspTemperatureIndigo == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE:
                state_to_update = "temperature"  # Primary device - Additional State
            secondary_dev_id = zd_dev.pluginProps.get("secondaryDeviceTemperatureSensor", 0)  # Returns int zero if no secondary temperature device
            if uspTemperatureIndigo == INDIGO_SECONDARY_DEVICE and secondary_dev_id != 0:
                if secondary_dev_id in indigo.devices:
                    zd_dev_to_process = indigo.devices[secondary_dev_id]
                    update_secondary_device = True
                    state_to_update = "sensorValue"  # Primary device
            if not zd_dev_to_process.enabled:
                return
            if uspTemperatureIndigo == INDIGO_SECONDARY_DEVICE and not update_secondary_device:
                self.zigbeeLogger.warning(f"received temperature event with a raw payload of \"{json_payload['temperature']}\" for a missing secondary device associated with device \"{zd_dev_to_process.name}\". Event discarded and ignored.")
                return

            # At this point we have a primary device 'zd_dev' and a 'zd_dev_to_process' device which can either be the primary devoice or a secondary device.
            # The "temperature" (primary) or "sensorValue" (secondary) state will be updated on the 'zd_dev_to_process' device if valid and has a changed value

            try:
                temperatureUnitsConversion = zd_dev.pluginProps.get("uspTemperatureUnitsConversion", "C")
                if temperatureUnitsConversion in ["C", "F>C"]:  # noqa [Duplicated code fragment!]
                    temperature_unit_ui = "°C"
                else:
                    temperature_unit_ui = "°F"

                if "device_temperature" in json_payload:
                    temperature = float(json_payload["device_temperature"])
                else:
                    temperature = float(json_payload["temperature"])

                if temperatureUnitsConversion == "C>F":
                    temperature = float(((float(temperature) * 9) / 5) + 32.0)
                elif temperatureUnitsConversion == "F>C":
                    temperature = float(((float(temperature) - 32.0) * 5) / 9)
                valid = True
            except ValueError:
                valid = False

            if not valid:
                self.zigbeeLogger.warning(f"received temperature event with an invalid payload of \"{json_payload['temperature']}\" for device \"{zd_dev.name}\". Event discarded and ignored.")
                return

            if valid:
                decimal_places = int(zd_dev.pluginProps.get("uspTemperatureDecimalPlaces", 0))
                temperature_value, ui_temperature_value = self.processDecimalPlaces(temperature, decimal_places, temperature_unit_ui, INDIGO_ONE_SPACE_BEFORE_UNITS)  # noqa: reference before assignment
                if state_to_update in zd_dev_to_process.states:
                    if zd_dev_to_process.states[state_to_update] != temperature_value:
                        self.key_value_lists[zd_dev_to_process.id].append({'key': state_to_update, 'value': temperature_value, 'uiValue': ui_temperature_value})
                        if state_to_update == "sensorValue":
                            zd_dev_to_process.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)
                        if not bool(zd_dev.pluginProps.get("hideTemperatureBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" temperature {ui_temperature_value}")
                    else:
                        if not bool(zd_dev.pluginProps.get("hideTemperatureBroadcast", False)):
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev.name}\" unchanged temperature {ui_temperature_value}")
                else:
                    self.zigbeeLogger.error(f"received \"{zd_dev_to_process.name}\" update of \"{ui_temperature_value}\" for missing temperature state.")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_vibration(self, zd_dev, json_payload):
        try:
            if not zd_dev.enabled:
                return
            if "vibration" in json_payload:
                if zd_dev.pluginProps.get("uspVibration", False):
                    state_on_off_state = zd_dev.states["onOffState"]
                    state_action = zd_dev.states["action"]
                    # on_off_state = False if json_payload["vibration"] == True else True  # TODO: Is this needed?
                    on_off_state_ui = "on" if json_payload["vibration"] == True else "off"
                    on_off_state = json_payload["vibration"]
                    if (on_off_state and state_action == "idle") or ((not on_off_state) and state_action != "idle"):
                        self.key_value_lists[zd_dev.id].append({'key': 'onOffState', 'value': on_off_state, 'uiValue': on_off_state_ui})
                        if not on_off_state:  # i.e. "off"
                            self.key_value_lists[zd_dev.id].append({"key": "action", "value": "idle"})
                        if not bool(zd_dev.pluginProps.get("hideVibrationBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev.name}\" vibration sensor '{on_off_state_ui}' event")
                    a = 1
                    b = a + 1
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_voltage(self, zd_dev, json_payload):
        try:
            if not zd_dev.pluginProps.get("uspVoltage", False) or not "voltage" in json_payload:
                return

            uspVoltageIndigo = zd_dev.pluginProps.get("uspVoltageIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE)
            zd_dev_to_process = zd_dev
            update_secondary_device = False
            state_to_update = "voltage"  # Primary device
            secondary_dev_id = zd_dev.pluginProps.get("secondaryDeviceVoltageSensor", 0)  # Returns int zero if no secondary voltage device
            if uspVoltageIndigo == INDIGO_SECONDARY_DEVICE and secondary_dev_id != 0:
                if secondary_dev_id in indigo.devices:
                    zd_dev_to_process = indigo.devices[secondary_dev_id]
                    update_secondary_device = True
                    state_to_update = "sensorValue"  # Primary device
            if not zd_dev_to_process.enabled:
                return
            if uspVoltageIndigo == INDIGO_SECONDARY_DEVICE and not update_secondary_device:
                self.zigbeeLogger.warning(f"received voltage event with a raw payload of \"{json_payload['voltage']}\" for a missing secondary device associated with device \"{zd_dev_to_process.name}\". Event discarded and ignored.")
                return

            # At this point we have a primary device 'zd_dev' and a 'zd_dev_to_process' device which can either be the primary devoice or a secondary device.
            # The "voltage" (primary) or "sensorValue" (secondary) state will be updated on the 'zd_dev_to_process' device if valid and has a changed value

            try:
                voltage = int(json_payload["voltage"])
                valid = True
            except ValueError:
                self.zigbeeLogger.warning(f"received voltage event with an invalid payload of \"{json_payload['voltage']}\" for device \"{zd_dev_to_process.name}\". Event discarded and ignored.")
                valid = False

            if valid:
                decimal_places = int(zd_dev.pluginProps.get("uspVoltageDecimalPlaces", 0))
                voltage_value, ui_voltage_value = self.processDecimalPlaces(voltage, decimal_places, "Volts", INDIGO_ONE_SPACE_BEFORE_UNITS)  # noqa: reference before assignment
                if state_to_update in zd_dev_to_process.states:
                    if zd_dev_to_process.states[state_to_update] != voltage_value:
                        self.key_value_lists[zd_dev_to_process.id].append({'key': state_to_update, 'value': voltage_value, 'uiValue': ui_voltage_value})
                        if not bool(zd_dev.pluginProps.get("hideVoltageBroadcast", False)):
                            self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" voltage {ui_voltage_value}")
                    else:
                        if not bool(zd_dev.pluginProps.get("hideVoltageBroadcast", False)):
                            if self.globals[DEBUG]: self.zigbeeLogger.info(f"received \"{zd_dev_to_process.name}\" unchanged voltage {ui_voltage_value}")
                else:
                    self.zigbeeLogger.error(f"received \"{zd_dev_to_process.name}\" update of \"{ui_voltage_value}\" for missing voltage state.")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement


    # if len(topics_list) == 5 and topics_list[4] == "status":
    #     with self.globals[LOCK_ZB_LINKED_INDIGO_DEVICES]:
    #         for dev_id in self.globals[ZB_HUBS][hub_name][ZB_DEVICES][zigbee_device_name][ZB_LINKED_INDIGO_DEVICES]:
    #             dev = indigo.devices[dev_id]
    #             if dev.pluginProps.get("uspContact", False):
    #                 if payload == "open":
    #                     dev.updateStateOnServer(key="onOffState", value=True)
    #                     if topics_list[3] in ZB_PRIMARY_INDIGO_DEVICE_TYPES_AND_HABITAT_PROPERTIES[dev.deviceTypeId]:
    #                         dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
    #                 else:
    #                     dev.updateStateOnServer(key="onOffState", value=False)
    #                     if topics_list[3] in ZB_PRIMARY_INDIGO_DEVICE_TYPES_AND_HABITAT_PROPERTIES[dev.deviceTypeId]:
    #                         dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
    #                 if not bool(dev.pluginProps.get("hideContactBroadcast", False)):
    #                     self.zigbeeLogger.info(f"received \"{dev.name}\" contact sensor \"{payload}\" event")

    #         # Check for HVAC Mode
    #         elif topics_list[3] == "mode":
    #             with self.globals[LOCK_ZB_LINKED_INDIGO_DEVICES]:
    #                 for dev_id in self.globals[ZB_HUBS][hub_name][ZB_DEVICES][zigbee_device_name][ZB_LINKED_INDIGO_DEVICES]:
    #                     dev = indigo.devices[dev_id]
    #                     if dev.deviceTypeId == "thermostat" and dev.pluginProps.get("uspHvacMode", False):
    #                         if payload == "off" or payload == "switched off":
    #                             indigo_state_value = indigo.kHvacMode.Off
    #                         elif payload == "heat":
    #                             indigo_state_value = indigo.kHvacMode.Heat
    #                         elif payload == "eco":
    #                             indigo_state_value = indigo.kHvacMode.Cool
    #                         elif payload == "auto":
    #                             indigo_state_value = indigo.kHvacMode.HeatCool
    #                         else:
    #                             self.zigbeeLogger.warning(f"received \"{dev.name}\" hvac unknown mode update: payload = '{payload}'")
    #                             return
    #
    #                         dev.updateStateOnServer(key='hvacMode', value=payload)
    #                         if not bool(dev.pluginProps.get("hideHvacModeBroadcast", False)):
    #                             dev.updateStateOnServer(key='hvacOperationMode', value=indigo_state_value)
    #                             self.zigbeeLogger.info(f"received \"{dev.name}\" hvac mode update to {payload}")
    #
    #         # Check for HVAC State
    #         elif topics_list[3] == "state":
    #             with self.globals[LOCK_ZB_LINKED_INDIGO_DEVICES]:
    #                 for dev_id in self.globals[ZB_HUBS][hub_name][ZB_DEVICES][zigbee_device_name][ZB_LINKED_INDIGO_DEVICES]:
    #                     dev = indigo.devices[dev_id]
    #                     if dev.subType == indigo.kDimmerDeviceSubType.Blind and dev.pluginProps.get("uspState", False):
    #                         dev.updateStateOnServer(key='state', value=payload)
    #                         if not bool(dev.pluginProps.get("hideStateBroadcast", False)):
    #                             self.zigbeeLogger.info(f"received \"{dev.name}\" state update to {payload}")
    #
    #         # Check for Setpoint
    #         elif topics_list[3] == "thermostat-setpoint":
    #             with self.globals[LOCK_ZB_LINKED_INDIGO_DEVICES]:
    #                 for dev_id in self.globals[ZB_HUBS][hub_name][ZB_DEVICES][zigbee_device_name][ZB_LINKED_INDIGO_DEVICES]:
    #                     dev = indigo.devices[dev_id]
    #                     if dev.pluginProps.get("uspSetpoint", False):
    #                         try:
    #                             setpointUnitsConversion = dev.pluginProps.get("uspSetpointUnitsConversion", "C")
    #                             if setpointUnitsConversion in ["C", "F>C"]:  # noqa [Duplicated code fragment!]
    #                                 setpoint_unit_ui = "°C"
    #                             else:
    #                                 setpoint_unit_ui = "°F"
    #                             if setpointUnitsConversion == "C>F":
    #                                 setpoint = float(((float(payload) * 9) / 5) + 32.0)
    #                             elif setpointUnitsConversion == "F>C":
    #                                 setpoint = float(((float(payload) - 32.0) * 5) / 9)
    #                             else:
    #                                 setpoint = float(payload)
    #                         except ValueError:
    #                             return
    #
    #                         decimal_places = int(dev.pluginProps.get("uspSetpointDecimalPlaces", 0))
    #                         value, uiValue = self.processDecimalPlaces(setpoint, decimal_places, setpoint_unit_ui, INDIGO_NO_SPACE_BEFORE_UNITS)
    #                         dev.updateStateOnServer(key='setpointHeat', value=value, uiValue=uiValue)
    #                         # if topics_list[3] in ZB_DEVICE_TYPES_MAIN_HABITAT_PROPERTIES[dev.deviceTypeId]:
    #                         #     dev.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensor)
    #                         if not bool(dev.pluginProps.get("hideSetpointBroadcast", False)):
    #                             self.zigbeeLogger.info(f"received \"{dev.name}\" setpoint update to {uiValue}")
    #

    def determine_secondary_device_id(self, dev_id, secondary_dev_type_id):
        try:
            # TODO: Use links stored in Primary
            dev_id_list = indigo.device.getGroupList(dev_id)
            secondary_dev_id = 0
            if len(dev_id_list) > 1:
                for grouped_dev_id in dev_id_list:
                    if grouped_dev_id != dev_id and indigo.devices[grouped_dev_id].deviceTypeId == secondary_dev_type_id:
                        secondary_dev_id = grouped_dev_id
                        break
            return secondary_dev_id

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def processDecimalPlaces(self, field, decimal_places, units, space_before_units):
        try:
            units_plus_optional_space = f" {units}" if space_before_units else f"{units}"  # noqa [Duplicated code fragment!]
            if decimal_places == 0:
                return int(field), f"{int(field)}{units_plus_optional_space}"
            else:
                if type(field) is float:
                    value = round(field, decimal_places)
                else:
                    # Assume field is an int
                    divisor = pow(10, decimal_places)
                    value = round((field / divisor), decimal_places)
                uiValue = "{{0:.{0}f}}{1}".format(decimal_places, units_plus_optional_space).format(value)

                return value, uiValue

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def mqtt_filter_log_processing(self, zigbee_coordinator_ieee, topic_friendly_name, topics, payload):
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
                self.zigbeeLogger.debug(f"MQTT logging for '{topic_friendly_name}': Topic='{topics}'\n          Payload='{payload}'\n")  # noqa [Unresolved attribute reference]

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
