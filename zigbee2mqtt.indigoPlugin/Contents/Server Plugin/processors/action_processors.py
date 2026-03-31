#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Action processor methods extracted from zigbeeHandler.py

from __future__ import annotations

import threading
from typing import Any, Dict, List

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import DEBUG, ZD_ROTATION_VARIABLE, ZD_ROTATION_INITIAL

class ActionProcessorMixin:
    """Mixin class containing action processing methods."""

    def process_property_action(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
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
                    number_of_buttons = self.validate_button_count(zd_dev.pluginProps, zd_dev.name)
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
                        self.zigbeeLogger.warning(f"Device '{zd_dev.name}' [{zd_dev.address}]: Button {button_number} not supported (device has {number_of_buttons} button(s)). Action '{button_action}' ignored.")
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_action_vibration(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
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

    def process_property_action_remote_audio(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
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

    def process_property_action_remote_dimmer(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
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

    def process_property_action_scene_rotary(self, zd_dev: Any, json_payload: Dict[str, Any], zd_dev_internal: Dict[str, Any]) -> None:
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

    def process_property_action_multi_switch(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
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

    def process_property_action_switch(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
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

    def process_property_action_idle_timer(self, parameters: List[Any]) -> None:
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

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def process_property_angles(self, zd_dev: Any, json_payload: Dict[str, Any]) -> None:
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

    def process_property_rotations(self, zd_dev: Any, json_payload: Dict[str, Any], zd_dev_internal: Dict[str, Any]) -> None:
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
