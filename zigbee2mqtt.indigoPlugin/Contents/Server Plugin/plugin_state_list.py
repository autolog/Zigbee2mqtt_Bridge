#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Device state list methods extracted from plugin.py

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import (
    INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE,
)


class StateListMixin:
    """Mixin class containing device state list methods."""

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

            # Action State [Remote Audio] [Ikea Symfonisk Remote] related States
            if bool(dev_plugin_props.get("uspRemoteAudio", False)):
                button_trigger_label = f"Action Changed"
                button_control_page_label = f"Action"
                action_state =  self.getDeviceStateDictForStringType("action", button_trigger_label, button_control_page_label)
                if action_state not in state_list:
                    state_list.append(action_state)
                button_state_id = "lastButtonPressed"
                button_trigger_label = "Last Button Pressed Changed"
                button_control_page_label = "Last Button Pressed"
                button_state = self.getDeviceStateDictForStringType(button_state_id, button_trigger_label, button_control_page_label)
                if button_state not in state_list:
                    state_list.append(button_state)

            # Action State [Remote Audio] [Ikea Styrbar Remote] related States
            if bool(dev_plugin_props.get("uspRemoteDimmer", False)):
                button_trigger_label = f"Action Changed"
                button_control_page_label = f"Action"
                action_state = self.getDeviceStateDictForStringType("action", button_trigger_label, button_control_page_label)
                if action_state not in state_list:
                    state_list.append(action_state)
                button_state_id = "lastButtonPressed"
                button_trigger_label = "Last Button Pressed Changed"
                button_control_page_label = "Last Button Pressed"
                button_state = self.getDeviceStateDictForStringType(button_state_id, button_trigger_label, button_control_page_label)
                if button_state not in state_list:
                    state_list.append(button_state)

            # Action State [Vibration]
            if bool(dev_plugin_props.get("uspVibration", False)):
                vibration_trigger_label = f"Action Changed"
                vibration_control_page_label = f"Action"
                action_state = self.getDeviceStateDictForStringType("action", vibration_trigger_label, vibration_control_page_label)
                if action_state not in state_list:
                    state_list.append(action_state)

            # Action State [Scene Rotary] [Aqara H1 Rotary Knob] related States
            if bool(dev_plugin_props.get("uspSceneRotary", False)):
                action_trigger_label = f"Action Changed"
                action_control_page_label = f"Action"
                action_state = self.getDeviceStateDictForStringType("action", action_trigger_label, action_control_page_label)
                if action_state not in state_list:
                    state_list.append(action_state)
                last_action_state_id = "lastAction"
                last_action_trigger_label = "Last Action Changed"
                last_action_control_page_label = "Last Action"
                last_action_state = self.getDeviceStateDictForStringType(last_action_state_id, last_action_trigger_label, last_action_control_page_label)
                if last_action_state not in state_list:
                    state_list.append(last_action_state)

            # Action State [Multi-Switch] [Aqara E1] related States
            if bool(dev_plugin_props.get("uspMultiSwitchAction", False)):
                action_trigger_label = f"Action Changed"
                action_control_page_label = f"Action"
                action_state = self.getDeviceStateDictForStringType("action", action_trigger_label, action_control_page_label)
                if action_state not in state_list:
                    state_list.append(action_state)
                last_action_state_id = "lastAction"
                last_action_trigger_label = "Last Action Changed"
                last_action_control_page_label = "Last Action"
                last_action_state = self.getDeviceStateDictForStringType(last_action_state_id, last_action_trigger_label, last_action_control_page_label)
                if last_action_state not in state_list:
                    state_list.append(last_action_state)

            # Action State [Switch] [Aqara E1] related States
            if bool(dev_plugin_props.get("uspSwitchAction", False)):
                action_trigger_label = f"Action Changed"
                action_control_page_label = f"Action"
                action_state = self.getDeviceStateDictForStringType("action", action_trigger_label, action_control_page_label)
                if action_state not in state_list:
                    state_list.append(action_state)
                last_action_state_id = "lastAction"
                last_action_trigger_label = "Last Action Changed"
                last_action_control_page_label = "Last Action"
                last_action_state = self.getDeviceStateDictForStringType(last_action_state_id, last_action_trigger_label, last_action_control_page_label)
                if last_action_state not in state_list:
                    state_list.append(last_action_state)

            # Angle States
            if bool(dev_plugin_props.get("uspAngles", False)):
                angle_state = self.getDeviceStateDictForStringType("angle", "Angle Changed", "Angle")
                angle_state_x = self.getDeviceStateDictForStringType("angle_x", "Angle_X Changed", "Angle_X")
                angle_x_absolute = self.getDeviceStateDictForStringType("angle_x_absolute", "Angle_X_Absolute Changed", "Angle_X_Absolute")
                angle_y = self.getDeviceStateDictForStringType("angle_y", "Angle_Y Changed", "Angle_Y")
                angle_y_absolute = self.getDeviceStateDictForStringType("angle_y_absolute", "Angle_Y_Absolute Changed", "Angle_Y_Absolute")
                angle_z = self.getDeviceStateDictForStringType("angle_z", "Angle_Z Changed", "Angle_Z")
                if angle_state not in state_list:
                    state_list.append(angle_state)
                if angle_state_x not in state_list:
                    state_list.append(angle_state_x)
                if angle_x_absolute not in state_list:
                    state_list.append(angle_x_absolute)
                if angle_y not in state_list:
                    state_list.append(angle_y)
                if angle_y_absolute not in state_list:
                    state_list.append(angle_y_absolute)
                if angle_z not in state_list:
                    state_list.append(angle_z)

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

            #  Presence Detection Options
            if (bool(dev_plugin_props.get("uspPresenceDetectionOptions", False)) and
                    dev_plugin_props.get("uspPresenceDetectionOptionsIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                presence_detection_options = self.getDeviceStateDictForBoolTrueFalseType("presenceDetectionOptions", "Presence Detection Options Changed", "Presence Detection Options")
                if presence_detection_options not in state_list:
                    state_list.append(presence_detection_options)

            # PIR Detection
            if (bool(dev_plugin_props.get("uspPirDetection", False)) and
                    dev_plugin_props.get("uspPirDetectionIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                pir_detection_state = self.getDeviceStateDictForBoolTrueFalseType("pirDetection", "PIR Detection Changed", "PIR Detection")
                if pir_detection_state not in state_list:
                    state_list.append(pir_detection_state)

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

            # Rotation States
            if bool(dev_plugin_props.get("uspRotations", False)):
                rotation_angle = self.getDeviceStateDictForStringType("rotation_angle", "Rotation Angle Changed", "Rotation Angle")
                rotation_angle_speed = self.getDeviceStateDictForStringType("rotation_angle_speed", "Rotation Angle Speed Changed", "Rotation Angle Speed")
                rotation_percent = self.getDeviceStateDictForStringType("rotation_percent", "Rotation Percent Changed", "Rotation Percent")
                rotation_percent_positive = self.getDeviceStateDictForStringType("rotation_percent_positive", "Rotation Percent Positive Changed", "Rotation Positive Percent")
                rotation_percent_speed = self.getDeviceStateDictForStringType("rotation_percent_speed", "Rotation Percent Speed Changed", "Rotation Percent Speed")
                rotation_time = self.getDeviceStateDictForStringType("rotation_time", "Rotation Time Changed", "Rotation Time")
                if rotation_angle not in state_list:
                    state_list.append(rotation_angle)
                if rotation_angle_speed not in state_list:
                    state_list.append(rotation_angle_speed)
                if rotation_percent not in state_list:
                    state_list.append(rotation_percent)
                if rotation_percent_positive not in state_list:
                    state_list.append(rotation_percent_positive)
                if rotation_percent_speed not in state_list:
                    state_list.append(rotation_percent_speed)
                if rotation_time not in state_list:
                    state_list.append(rotation_time)

            # State  [used by Blind]
            if bool(dev_plugin_props.get("uspState", False)):
                state_state = self.getDeviceStateDictForStringType("state", "State Mode Changed", "State")  # TODO: Check type is correct and whether it should be internal onOffState
                if state_state not in state_list:
                    state_list.append(state_state)

            # Strength State [Vibration]
            if bool(dev_plugin_props.get("uspStrength", False)):
                strength_trigger_label = f"Strength Changed"
                strength_control_page_label = f"Strength"
                strength_state = self.getDeviceStateDictForStringType("strength", strength_trigger_label, strength_control_page_label)
                if strength_state not in state_list:
                    state_list.append(strength_state)

            # Target Distance State
            if (bool(dev_plugin_props.get("uspTargetDistance", False)) and
                    dev_plugin_props.get("uspTargetDistanceIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                target_distance_state = self.getDeviceStateDictForNumberType("targetDistance", "Target Distance Changed", "Target Distance")
                if target_distance_state not in state_list:
                    state_list.append(target_distance_state)

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

            # Voltage State (duplicate check - keeping for compatibility)
            if (bool(dev_plugin_props.get("uspVoltage", False)) and
                    dev_plugin_props.get("uspVoltageIndigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE) == INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE):
                voltage_state = self.getDeviceStateDictForNumberType("voltage", "Voltage Changed", "Voltage")
                if voltage_state not in state_list:
                    state_list.append(voltage_state)

            return state_list
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def list_device_state_menu_options(self, filter="", values_dict=None, type_id="", target_id=0):   # noqa [parameter value is not used]
        try:
            # <Option value="0">Primary Device - Main UI State</Option>
            # <Option value="1">Primary Device - Additional State</Option>
            # <Option value="2">Secondary Device</Option>
            # <Option value="3">Primary Device - Additional UI State</Option>

            # if self.globals[DEBUG]: self.logger.error(f"list_device_state_menu_options. filter='{filter}', type_id='{type_id}'")

            # dev = indigo.devices[target_id]

            if ((filter == "button" and type_id == "button") or
                    (filter == "contact" and type_id == "contactSensor") or
                    (filter == "water_leak" and type_id == "waterLeakSensor") or
                    (filter == "SceneRotary" and type_id == "sceneRotary") or  # TODO: Sort out for SceneRotary device
                    (filter == "blind" and type_id == "blind") or
                    (filter == "brightness" and type_id == "dimmer") or
                    (filter == "brightnessL1" and type_id == "multiDimmer") or
                    (filter == "onoff" and type_id == "dimmer") or
                    (filter == "humiditySensor" and type_id == "humiditySensor") or
                    (filter == "illuminanceSensor" and type_id == "illuminanceSensor") or
                    (filter == "motionSensor" and type_id == "motionSensor") or
                    (filter == "motionSensor" and type_id == "multiSensor") or
                    (filter == "multiSwitch" and type_id == "multiSwitch") or
                    (filter == "onoff" and type_id == "outlet") or
                    (filter == "presenceSensor" and type_id == "presenceSensor") or
                    (filter == "radarSensor" and type_id == "radarSensor") or
                    (filter == "remoteAudio" and type_id == "remoteAudio") or
                    (filter == "remoteDimmer" and type_id == "remoteDimmer") or
                    (filter == "stateL1" and type_id == "multiDimmer") or
                    (filter == "stateL1" and type_id == "multiOutlet") or
                    (filter == "stateLeft" and type_id == "multiSocket") or
                    (filter == "strength" and type_id == "strength") or
                    (filter == "switch" and type_id == "switch") or
                    (filter == "temperatureSensor" and type_id == "temperatureSensor") or
                    (filter == "temperatureSensor" and type_id == "thermostat") or
                    (filter == "vibrationSensor" and type_id == "vibrationSensor")):
                menu_list = [("0", "Primary Device - Main UI State")]
            elif ((filter == "link-quality") or
                  (filter == "last_seen") or
                  (filter == "angles" and type_id == "vibrationSensor") or
                  (filter == "setpoint" and type_id == "thermostat") or
                  (filter == "onoff" and type_id == "thermostat") or
                  (filter == "onoff" and type_id == "blind") or
                  (filter == "color" and type_id == "dimmer") or
                  (filter == "colorTemperature" and type_id == "dimmer") or
                  (filter == "onoff" and type_id == "dimmer") or
                  (filter == "rotations" and type_id == "sceneRotary") or
                  (filter == "targetDistance" and type_id == "radarSensor") or
                  (filter == "powerLeft")):
                menu_list = [("1", "Primary Device - Additional State")]
            elif ((filter == "stateL2-5") or
                  (filter == "brightnessL2-3") or
                  (filter == "stateRight") or
                  (filter == "stateLeft")):
                menu_list = [("2", "Secondary Device")]
            elif filter == "powerRight":
                menu_list = [("3", "Secondary Device - Additional State")]
            else:
                menu_list = [("1", "Primary Device - Additional State"), ("2", "Secondary Device")]
            return menu_list

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
