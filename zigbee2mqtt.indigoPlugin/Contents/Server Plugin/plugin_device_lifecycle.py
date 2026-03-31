#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Device lifecycle methods extracted from plugin.py

import json
import queue
import threading

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from coordinatorHandler import ThreadCoordinatorHandler
from zigbeeHandler import ThreadZigbeeHandler

from constants import (
    CH_EVENT,
    CH_THREAD,
    LOCK_ZC,
    MQTT_CLIENT_ID,
    MQTT_CLIENT_PREFIX,
    MQTT_ENCRYPTION_KEY,
    MQTT_FILTERS,
    MQTT_IP,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_PROTOCOL,
    MQTT_ROOT_TOPIC,
    MQTT_ROOT_TOPIC_DEFAULT,
    MQTT_USERNAME,
    MQTT_ZIGBEE2MQTT_QUEUE,
    QUEUES,
    ZC,
    ZC_TO_INDIGO_ID,
    ZD,
    ZD_FRIENDLY_NAME,
    ZD_INDIGO_DEVICE_ID,
    ZD_MESSAGE_COUNT,
    ZD_SOFTWARE_BUILD_ID,
    ZD_TO_INDIGO_ID,
    ZG,
    ZG_INDIGO_DEVICE_ID,
    ZH_EVENT,
    ZH_THREAD,
)


class DeviceLifecycleMixin:
    """Mixin class containing device start/stop/update/delete methods."""

    def device_start_comm(self, dev):
        try:

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

            for zigbee_coordinator_ieee in self.globals[ZD]:
                for zigbee_device_ieee in self.globals[ZD][zigbee_coordinator_ieee]:
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] = 0
                    # Added 2024-12-28
                    if ZD_FRIENDLY_NAME not in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                        self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] = f"!!! {zigbee_device_ieee}"

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
                        except (ValueError, json.JSONDecodeError, KeyError, TypeError):
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

            if "zigbeePropertiesInitialised" not in zd_dev_props or not zd_dev_props["zigbeePropertiesInitialised"]:
                self.logger.warning(f"Zigbee Device {zd_dev.name} has not been initialised - Edit and Save device Settings for device.")
                return

            # Now process any existing or required secondary devices

            self.process_secondary_devices(zd_dev, zigbee_coordinator_ieee, update_device_name)

            # Check if secondary device(s) required to be created and create as necessary

            if zigbee_coordinator_ieee not in self.globals[ZD]:
                self.logger.warning(f"'" + zd_dev.name + "'zigbee_coordinator_ieee not in self.globals[ZD]: '" + zigbee_coordinator_ieee + "'")
                self.globals[ZD][zigbee_coordinator_ieee] = dict()  # Zigbee Coordinator
            if zigbee_device_ieee not in self.globals[ZD][zigbee_coordinator_ieee]:
                self.logger.warning(f"'" + zd_dev.name + "'zigbee_device_ieee not in self.globals[ZD][zigbee_coordinator_ieee]: '" + zigbee_device_ieee + "'")
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
                                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] = 0

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        super().deviceDeleted(dev)

    def device_stop_comm(self, dev):
        try:
            match dev.deviceTypeId:
                case "zigbeeCoordinator":
                    # DEBUG self.logger.error("COORDINATOR STOPPED [1]")
                    if CH_EVENT in self.globals[ZC][dev.id]:
                        # DEBUG self.logger.error("COORDINATOR STOPPED [2]")
                        self.globals[ZC][dev.id][CH_EVENT].set()  # Stop the MQTT Client
                        self.globals[ZC][dev.id][CH_THREAD].join(10.0)  # Allow up to n seconds for MQTT Client thread to stop
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

        super().deviceUpdated(origDev, newDev)
