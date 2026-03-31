#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Config UI methods extracted from plugin.py

import json
import re
import socket

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import (
    DEBUG,
    INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE,
    INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE,
    INDIGO_SECONDARY_DEVICE,
    INDIGO_SECONDARY_DEVICE_ADDITIONAL_STATE,
    LOCK_ZC,
    LOG_LEVEL_INFO,
    LOG_LEVEL_TRANSLATION,
    MQTT_CLIENT_ID,
    MQTT_CLIENT_PREFIX,
    MQTT_ENCRYPTION_KEY,
    MQTT_IP,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_PROTOCOL,
    MQTT_ROOT_TOPIC,
    MQTT_ROOT_TOPIC_DEFAULT,
    MQTT_SUPPRESS_IEEE_MISSING,
    MQTT_USERNAME,
    ZC,
    ZC_LIST,
    ZD,
    ZD_INDIGO_DEVICE_ID,
    ZD_MESSAGE_COUNT,
    ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES,
)

from cryptography_support import decode, encode


class ConfigUIMixin:
    """Mixin class containing config UI validation and callback methods."""

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

            zigbee_coordinator_ieee = values_dict["zigbee_coordinator_ieee"]
            if zigbee_coordinator_ieee != "":
                zigbee_device_ieee = values_dict["zigbee_device_ieee"]
                if zigbee_device_ieee != "":
                    if zigbee_coordinator_ieee in self.globals[ZD]:
                        if zigbee_device_ieee in self.globals[ZD][zigbee_coordinator_ieee]:
                            self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_INDIGO_DEVICE_ID] = dev_id
                            self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] = 0

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
                case "multiDimmer":
                    pass
                case "multiOutlet":
                    pass
                case "multiSensor":
                    pass
                case "multiSocket":
                    pass
                case "multiSwitch":
                    pass
                case "presenceSensor":
                    pass
                case "radarSensor":
                    pass
                case "remoteAudio":
                    pass
                case "remoteDimmer":
                    pass
                case "sceneRotary":
                    pass
                case "switch":
                    pass
                case "temperatureSensor":
                    pass
                case "thermostat":
                    pass
                case "vibrationSensor":
                    pass
                case "waterLeakSensor":
                    pass
                case "accelerationSensorSecondary":
                    pass
                case "humiditySensorSecondary":
                    pass
                case "illuminanceSensorSecondary":
                    pass
                case "motionSensorSecondary":
                    pass
                case "multiSwitchSecondaryLeft":
                    pass
                case "multiSwitchSecondaryRight":
                    pass
                case "presenceSensorSecondary":
                    pass
                case "pressureSensorSecondary":
                    pass
                case "switchSecondarySingle":
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

    def get_action_config_ui_values(self, plugin_props, type_id="", dev_id=0):
        try:
            if type_id == "setWhiteLevelTemperature":
                try:
                    dimmer_device_id = int(plugin_props.get("dimmer_device_id", ""))
                except ValueError:
                    plugin_props["dimmer_device_id"] = "SELECT"

            return super().getActionConfigUiValues(plugin_props, type_id, dev_id)

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

                if "mqtt_password_is_encoded" not in plugin_props:
                    plugin_props["mqtt_password_is_encoded"] = False
                if "mqtt_password" in plugin_props and plugin_props["mqtt_password_is_encoded"]:
                    plugin_props["mqtt_password_is_encoded"] = False
                    mqtt_password_encryption_key = plugin_props.get("mqtt_password_encryption_key", "")
                    plugin_props["mqtt_password"] = decode(mqtt_password_encryption_key.encode('utf-8'), plugin_props["mqtt_password"].encode('utf-8'))

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
                    plugin_props["zigbeePropertyBrightnessL1"] = False
                    plugin_props["zigbeePropertyBrightnessL2"] = False
                    plugin_props["zigbeePropertyBrightnessL3"] = False
                    plugin_props["zigbeePropertyAction"] = False
                    plugin_props["zigbeePropertyAngles"] = False
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
                    plugin_props["zigbeePropertyMultiSwitchAction"] = False
                    plugin_props["zigbeePropertyPosition"] = False
                    plugin_props["zigbeePropertyPower"] = False
                    plugin_props["zigbeePropertyPower_left"] = False
                    plugin_props["zigbeePropertyPower_right"] = False

                    plugin_props["zigbeePropertyPresenceDetectionOptions"] = False
                    plugin_props["zigbeePropertyPirDetection"] = False

                    plugin_props["zigbeePropertyPresence"] = False
                    plugin_props["zigbeePropertyPressure"] = False
                    plugin_props["zigbeePropertyRadar"] = False
                    plugin_props["zigbeePropertyRotations"] = False
                    plugin_props["zigbeePropertySceneRotary"] = False
                    plugin_props["zigbeePropertySetpoint"] = False
                    plugin_props["zigbeePropertySwitchAction"] = False
                    plugin_props["zigbeePropertyHvacState"] = False
                    plugin_props["zigbeePropertyState"] = False
                    plugin_props["zigbeePropertyStateL1"] = False
                    plugin_props["zigbeePropertyStateL2"] = False
                    plugin_props["zigbeePropertyStateL3"] = False
                    plugin_props["zigbeePropertyStateL4"] = False
                    plugin_props["zigbeePropertyStateL5"] = False
                    plugin_props["zigbeePropertyStateLeft"] = False
                    plugin_props["zigbeePropertyStateRight"] = False
                    plugin_props["zigbeePropertyStateSingle"] = False
                    plugin_props["zigbeePropertyStrength"] = False
                    plugin_props["zigbeePropertyTamper"] = False
                    plugin_props["zigbeePropertyTemperature"] = False
                    plugin_props["zigbeePropertyValve"] = False
                    plugin_props["zigbeePropertyVibration"] = False
                    plugin_props["zigbeePropertyVoltage"] = False
                    plugin_props["zigbeePropertyWaterLeak"] = False

                    plugin_props["uspAcceleration"] = False
                    plugin_props["uspBattery"] = False
                    plugin_props["uspBrightness"] = False
                    plugin_props["uspBrightnessL1"] = False
                    plugin_props["uspBrightnessL2"] = False
                    plugin_props["uspBrightnessL3"] = False
                    plugin_props["uspAction"] = False
                    plugin_props["uspAngles"] = False
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
                    plugin_props["uspRotations"] = False
                    plugin_props["uspSceneRotary"] = False
                    plugin_props["uspSetpoint"] = False
                    plugin_props["uspState"] = False
                    plugin_props["uspStateL1"] = False
                    plugin_props["uspStateL2"] = False
                    plugin_props["uspStateL3"] = False
                    plugin_props["uspStateL4"] = False
                    plugin_props["uspStateL5"] = False
                    plugin_props["uspStateLeft"] = False
                    plugin_props["uspStateRight"] = False
                    plugin_props["uspStrength"] = False
                    plugin_props["uspTamper"] = False
                    plugin_props["uspTemperature"] = False
                    plugin_props["uspValve"] = False
                    plugin_props["uspVibration"] = False
                    plugin_props["uspVoltage"] = False
                    plugin_props["uspColorTemperature"] = False

                if "UpdateNotesJsonList" not in plugin_props or plugin_props["UpdateNotesJsonList"] == "":
                    plugin_props["UpdateNotesJsonList"] = "SELECT"

            elif type_id in ("accelerationSensorSecondary", "humiditySensorSecondary", "illuminanceSensorSecondary", "motionSensorSecondary",
                             "multiDimmerSecondary2", "multiDimmerSecondary3",
                             "multiOutletSecondary2", "multiOutletSecondary3", "multiOutletSecondary4", "multiOutletSecondary5",
                             "multiSocketSecondary", "multiSwitchSecondaryLeft", "multiSwitchSecondaryRight",
                             "presenceSensorSecondary", "pressureSensorSecondary", "switchSecondarySingle",
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

            return super().get_device_config_ui_values(plugin_props, type_id, dev_id)

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
                case "multiDimmer":
                    usp_primary_device_main_ui_state = "uspStateL1Indigo"
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
                case "multiSwitch":
                    usp_primary_device_main_ui_state = "uspActionIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                    values_dict["uspStateLeftIndigo"] = INDIGO_SECONDARY_DEVICE
                    values_dict["uspStateRightIndigo"] = INDIGO_SECONDARY_DEVICE
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
                case "remoteAudio":
                    usp_primary_device_main_ui_state = "uspRemoteAudioIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "remoteDimmer":
                    usp_primary_device_main_ui_state = "uspRemoteDimmerIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                case "sceneRotary":
                    usp_primary_device_main_ui_state = "uspSceneRotaryIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE

                case "switch":
                    usp_primary_device_main_ui_state = "uspSwitchActionIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
                    values_dict["uspStateSingleIndigo"] = INDIGO_SECONDARY_DEVICE
                    values_dict["uspLinkQualityIndigo"] = INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE

                    uspTemperatureIndigo = values_dict.get("uspTemperatureIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE)
                    if uspTemperatureIndigo not in [INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE, INDIGO_SECONDARY_DEVICE]:
                        uspTemperatureIndigo = INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE
                    values_dict["uspTemperatureIndigo"] = uspTemperatureIndigo

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
                case "waterLeakSensor":
                    usp_primary_device_main_ui_state = "uspWaterLeakIndigo"
                    usp_primary_device_main_ui_states.append(usp_primary_device_main_ui_state)
                    values_dict[usp_primary_device_main_ui_state] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE

            if type_id == "multiSocket" or type_id == "multiSwitch" or type_id == "multiDimmer" or type_id == "switch":
                pass
            else:
                for usp_field_id in ("uspAccelerationIndigo", "uspActionIndigo", "uspAnglesIndigo",
                                     "uspBrightnessIndigo", "uspBrightnessL1Indigo", "uspBrightnessL2Indigo", "uspBrightnessL3Indigo",
                                     "uspColorIndigo", "uspColorTemperatureIndigo",
                                     "uspContactIndigo", "uspEnergyIndigo", "uspHumidityIndigo", "uspIlluminanceIndigo", "uspLinkQualityIndigo", "uspOccupancyIndigo",
                                     "uspOnOffIndigo",
                                     "uspPositionIndigo", "uspPowerIndigo", "uspPowerLeftIndigo", "uspPowerRightIndigo",
                                     "uspPresenceDetectionOptionsIndigo", "uspPirDetectionIndigo", "uspPresenceIndigo", "uspPresenceEventIndigo", "uspPressureIndigo",
                                     "uspRadarIndigo", "uspRemoteAudioIndigo", "uspRemoteADimmerIndigo", "uspRotationsIndigo",
                                     "uspStateIndigo", "uspStateL2Indigo", "uspStateL3Indigo", "uspStateL4Indigo", "uspStateL5Indigo", "uspStateRightIndigo", "uspStateSingleIndigo",
                                     "uspStrengthIndigo", "uspTamperIndigo", "uspTemperatureIndigo", "uspSetpointIndigo", "uspValveIndigo", "uspVibrationIndigo", "uspVoltageIndigo", "uspWaterLeakIndigo"):
                    if usp_field_id not in usp_primary_device_main_ui_states:
                        if usp_field_id not in values_dict or values_dict[usp_field_id] not in [INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE, INDIGO_SECONDARY_DEVICE]:
                            values_dict[usp_field_id] = INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE  # Default

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
                    except:
                        values_dict["show_update_notes_json"] = False
            else:
                values_dict["show_update_notes_json"] = False

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        return values_dict, errors_dict

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

                case "multiDimmer":
                    # Multi-Dimmer (Light) validation and option settings
                    if not values_dict.get("uspStateL1", False):
                        error_message = "An Indigo Multi-Dimmer (Light) device requires an association to the Zigbee 'state_l1' property"
                        error_dict['uspStateL1'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        values_dict["SupportsStatusRequest"] = True

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

                case "multiSwitch":
                    # Multi-Switch validation and option settings
                    if not values_dict.get("uspMultiSwitchAction", False):
                        if values_dict["zigbee_vendor"].lower() == "tuya" and values_dict["zigbee_model"].lower() == "ts0012":
                            pass
                        elif values_dict["zigbee_vendor"].lower() != "moes":
                            pass
                        else:
                            error_message = "An Indigo Multi-Switch device requires an association to the Zigbee 'action' property"
                            error_dict['uspMultiSwitchAction'] = error_message
                            error_dict["showAlertText"] = error_message

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

                case "remoteAudio":
                    # Scene (Action) validation and option settings
                    if not values_dict.get("uspRemoteAudio", False):
                        error_message = "An Indigo remote [Audio] device requires an association to the Zigbee 'action' property"
                        error_dict['uspAction'] = error_message
                        error_dict["showAlertText"] = error_message

                case "remoteDimmer":
                    # Scene (Action) validation and option settings
                    if not values_dict.get("uspRemoteDimmer", False):
                        error_message = "An Indigo remote [Dimmer] device requires an association to the Zigbee 'action' property"
                        error_dict['uspAction'] = error_message
                        error_dict["showAlertText"] = error_message

                case "sceneRotary":
                    # Scene Rotary validation and option settings
                    if not values_dict.get("uspSceneRotary", False):
                        error_message = "An Indigo Scene Rotary device requires an association to the Zigbee 'action' property"
                        error_dict['uspSceneRotary'] = error_message
                        error_dict["showAlertText"] = error_message

                case "switch":
                    # Switch validation and option settings
                    if not values_dict.get("uspSwitchAction", False):
                        error_message = "An Indigo Switch device requires an association to the Zigbee 'action' property"
                        error_dict['uspSwitchAction'] = error_message
                        error_dict["showAlertText"] = error_message

                case "thermostat":
                    pass

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

                case "waterLeakSensor":
                    # Water Leak Sensor validation and option settings
                    if not values_dict.get("uspWaterLeak", False):
                        error_message = "An Indigo Water Leak Sensor device requires an association to the Zigbee 'water_leak' property"
                        error_dict['uspWaterLeak'] = error_message
                        error_dict["showAlertText"] = error_message
                    else:
                        values_dict["SupportsOnState"] = True
                        values_dict["allowOnStateChange"] = False

            return values_dict, error_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def validate_prefs_config_ui(self, values_dict):  # noqa [Method is not declared static]
        try:
            return True, values_dict

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
