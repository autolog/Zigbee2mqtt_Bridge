#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Device action methods extracted from plugin.py

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import (
    DEBUG,
    MQTT_ROOT_TOPIC,
    ZC,
    ZC_TO_INDIGO_ID,
    ZD,
    ZD_FRIENDLY_NAME,
)


class ActionsMixin:
    """Mixin class containing device action control methods."""

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
                if ZD_FRIENDLY_NAME in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                    friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME]
                else:
                    self.logger.warning(
                        f"Action Control Device '{dev.name}': Friendly name missing for zigbee device with address: {zigbee_device_ieee}")
                    self.logger.warning(
                        f"Unhandled \"actionControlDevice\" action \"{action.deviceAction}\" for \"{dev.name}\"")
                    return

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
                    case "multiDimmer":
                        topic_payload = '{"state_l1": "ON"}'
                        action_request = True
                    case "multiDimmerSecondary2" | "multiDimmerSecondary3":
                        switch_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "2" or "3"
                        topic_payload = f'{{"state_l{switch_number}": "ON"}}'
                        action_request = True
                    case "multiSocket":
                        topic_payload = '{"state_left": "ON"}'
                        action_request = True
                    case "multiSocketSecondary":
                        topic_payload = '{"state_right": "ON"}'
                        action_request = True
                    case "multiSwitchSecondaryLeft":
                        topic_payload = '{"state_left": "ON"}'
                        action_request = True
                    case "multiSwitchSecondaryRight":
                        topic_payload = '{"state_right": "ON"}'
                        action_request = True
                    case "switchSecondarySingle":
                        topic_payload = '{"state": "ON"}'
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
                    case "multiDimmer":
                        topic_payload = '{"state_l1": "OFF"}'
                        action_request = True
                    case "multiDimmerSecondary2" | "multiDimmerSecondary3":
                        switch_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "2" or "3"
                        topic_payload = f'{{"state_l{switch_number}": "OFF"}}'
                        action_request = True
                    case "multiSocket":
                        topic_payload = '{"state_left": "OFF"}'
                        action_request = True
                    case "multiSocketSecondary":
                        topic_payload = '{"state_right": "OFF"}'
                        action_request = True
                    case "multiSwitchSecondaryLeft":
                        topic_payload = '{"state_left": "OFF"}'
                        action_request = True
                    case "multiSwitchSecondaryRight":
                        topic_payload = '{"state_right": "OFF"}'
                        action_request = True
                    case "switchSecondarySingle":
                        topic_payload = '{"state": "OFF"}'
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
                        case "multiDimmer":
                            topic_payload = '{"state_l1": "OFF"}'
                            action_request = True
                        case "multiDimmerSecondary2" | "multiDimmerSecondary3":
                            switch_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "2" or "3"
                            topic_payload = f'{{"state_l{switch_number}": "OFF"}}'
                            action_request = True
                        case "multiSocket":
                            topic_payload = '{"state_left": "OFF"}'
                            action_request = True
                        case "multiSocketSecondary":
                            topic_payload = '{"state_right": "OFF"}'
                            action_request = True
                        case "multiSwitchSecondaryLeft":
                            topic_payload = '{"state_left": "OFF"}'
                            action_request = True
                        case "multiSwitchSecondaryRight":
                            topic_payload = '{"state_right": "OFF"}'
                            action_request = True
                        case "switchSecondarySingle":
                            topic_payload = '{"state": "OFF"}'
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
                        case "multiDimmer":
                            topic_payload = '{"state_l1": "ON"}'
                            action_request = True
                        case "multiDimmerSecondary2" | "multiDimmerSecondary3":
                            switch_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "2" or "3"
                            topic_payload = f'{{"state_l{switch_number}": "ON"}}'
                            action_request = True
                        case "multiSocket":
                            topic_payload = '{"state_left": "ON"}'
                            action_request = True
                        case "multiSocketSecondary":
                            topic_payload = '{"state_right": "ON"}'
                            action_request = True
                        case "multiSwitchSecondaryLeft":
                            topic_payload = '{"state_left": "ON"}'
                            action_request = True
                        case "multiSwitchSecondaryRight":
                            topic_payload = '{"state_right": "ON"}'
                            action_request = True
                        case "switchSecondarySingle":
                            topic_payload = '{"state": "ON"}'
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
                match dev.deviceTypeId:
                    case "dimmer" | "zigbeeGroupDimmer":
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
                    case "multiDimmer" | "multiDimmerSecondary2" | "multiDimmerSecondary3":
                        new_brightness = int(action.actionValue)   # action.actionValue contains brightness value (0 - 100)
                        action_ui = "set"
                        if new_brightness > 0:
                            if new_brightness > dev.brightness:
                                action_ui = "brighten"
                            else:
                                action_ui = "dim"
                        new_brightness_ui = f"{new_brightness}%"
                        new_brightness_255 = int((new_brightness * 255) / 100)
                        dimmer_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "1", "2" or "3"
                        topic_payload = f'{{"brightness_l{dimmer_number}": {new_brightness_255}}}'
                        self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)

                        self.logger.info(f"sending \"{action_ui} to {new_brightness_ui}\" to \"{dev.name}\"")
                    case "blind":
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
                match dev.deviceTypeId:
                    case "dimmer" | "zigbeeGroupDimmer":
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
                    case "multiDimmer" | "multiDimmerSecondary2" | "multiDimmerSecondary3":
                        if dev.brightness < 100:
                            brighten_by = int(action.actionValue)  # action.actionValue contains brightness increase value
                            new_brightness = dev.brightness + brighten_by
                            if new_brightness > 100:
                                new_brightness = 100
                            brighten_by_ui = f"{brighten_by}%"
                            new_brightness_255 = int((new_brightness * 255) / 100)
                            new_brightness_ui = f"{new_brightness}%"
                            dimmer_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "1", "2" or "3"
                            topic_payload = f'{{"brightness_l{dimmer_number}": {new_brightness_255}}}'
                            self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                            self.logger.info(f"sending brighten by {brighten_by_ui} to {new_brightness_ui}\" to \"{dev.name}\"")
                        else:
                            self.logger.info(f"Ignoring brighten request for \"{dev.name}\" as device is already at full brightness")
                    case "blind":
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
                match dev.deviceTypeId:
                    case "dimmer" | "zigbeeGroupDimmer":
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
                    case "multiDimmer" | "multiDimmerSecondary2" | "multiDimmerSecondary3":
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
                                dimmer_number = dev.deviceTypeId[-1]  # Get last character from deviceTypeId i.e. "1", "2" or "3"
                                topic_payload = f'{{"brightness_l{dimmer_number}": {new_brightness_255}}}'
                                self.publish_zigbee_topic(zigbee_coordinator_ieee, friendly_name, topic, topic_payload)
                                self.logger.info(f"sending \"dim by {dim_by_ui} to {new_brightness_ui}\" to \"{dev.name}\"")
                        else:
                            self.logger.info(f"Ignoring dim request for '{dev.name}'' as device is already Off")
                    case "blind":
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
