#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# List generator methods extracted from plugin.py

import json

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import (
    DEBUG,
    INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE,
    ZC_LIST,
    ZD,
    ZD_DEFINITION,
    ZD_DESCRIPTION_HW,
    ZD_DESCRIPTION_USER,
    ZD_EXPOSES,
    ZD_FRIENDLY_NAME,
    ZD_INDIGO_DEVICE_ID,
    ZD_MODEL,
    ZD_PRIMARY_INDIGO_DEVICE_TYPES_AND_ZIGBEE_PROPERTIES,
    ZD_PROPERTIES,
    ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES,
    ZD_VENDOR,
    ZG,
    ZG_MEMBERS,
)


class ListGeneratorsMixin:
    """Mixin class containing UI list generator methods and selection callbacks."""

    def menu_available_indigo_devices_filter_changed(self, values_dict, type_id, devId):
        # To force Dynamic Reload of devices
        pass
        return values_dict

    def available_indigo_devices_selected(self, values_dict, type_id, devId):
        # To force Dynamic Reload of devices

        # print(values_dict)
        pass
        return values_dict

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

    def list_rotation_variables(self, filter="", values_dict=None, type_id="", target_id=0):  # noqa [parameter value is not used]
        try:
            self.globals[ZC_LIST] = list()

            variables_list = list()
            variables_list.append((0, "-- Select Rotation Variable --"))
            for variable in indigo.variables.iter("self"):
                variables_list.append((variable.id, variable.name))
            if len(variables_list) == 2:
                del variables_list[0]
                return variables_list
            elif len(variables_list) > 2:
                return sorted(variables_list, key=lambda name: name[1].lower())   # sort by Zigbee Coordinator name
            else:
                variables_list = list()
                variables_list.append(("-NONE-", "No Variables available"))
                return variables_list
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def list_rotation_variable_selected(self, values_dict, type_id, dev_id):  # noqa [parameter value is not used]
        try:
            # do whatever you need to here
            #   type_id is the device type specified in the Devices.xml
            #   devId is the device ID - 0 if it's a new device
            self.logger.debug(f"Rotation Variable Selected: {values_dict['uspRotationPercentPositiveVariableId']}")

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

        return values_dict

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
            self.logger.debug(f"Zigbee Coordinator Selected: {values_dict['zigbee_coordinator_ieee']}")

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
                # self.logger.warning(f"list_zigbee_coordinator_devices: {zigbee_device_ieee}")  # Debug 2024-12-28
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
            # Never return raw XML with the $PROPERTY$ placeholder — Indigo rejects it
            # with "Fields must contain a 'type' attribute". Fall back to a stripped dialog.
            try:
                raw = self.devicesTypeDict[type_id]["ConfigUIRawXml"]
                return raw.replace("<Field>$PROPERTY$</Field>", "")
            except Exception:
                return ""

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
            # self.logger.warning(f"List of allocated Devices: {allocated_devices}")  # Debug

            # zigbee_dev = indigo.devices[target_id]

            zigbee_device_filter = "ALL"

            zigbee_devices_list.append(("-SELECT-", "-- Select Zigbee Device --"))
            for zigbee_device_ieee, zigbee_device_info in self.globals[ZD][zigbee_coordinator_ieee].items():
                if zigbee_device_ieee != "":
                    if ZD_INDIGO_DEVICE_ID not in zigbee_device_info:
                        self.logger.warning(f"No Indigo Device ID for IEEE Address: '" + zigbee_device_ieee + "'" + ", Length of 'zigbee_device_info': " +  str(len(zigbee_device_info)) + ", Length of 'self.globals[ZD][zigbee_coordinator_ieee]': " + str(len(self.globals[ZD][zigbee_coordinator_ieee])))
                        continue
                    if ZD_FRIENDLY_NAME not in zigbee_device_info:  # Fix for https://forums.indigodomo.com/viewtopic.php?t=28682
                        self.logger.warning(f"No Friendly Name ID for IEEE Address: {zigbee_device_ieee}, Indigo Device Id: {zigbee_device_info[ZD_INDIGO_DEVICE_ID]}")
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
                if ZD_DEFINITION not in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION] = dict()
                zigbee_hw = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION].get(ZD_DESCRIPTION_HW, "-")
                zigbee_model = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION].get(ZD_MODEL, "Unknown")
                zigbee_vendor = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_DEFINITION].get(ZD_VENDOR, "Unknown")
                if ZD_FRIENDLY_NAME not in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME] = f"!!! {zigbee_device_ieee}"
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

            if ZD_PROPERTIES not in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                return

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

                    case "brightness_l1":
                        if type_id == "multiDimmer":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyBrightnessL1"] = True
                            else:
                                values_dict["zigbeePropertyBrightnessL1"] = False
                    case "brightness_l2":
                        if type_id == "multiDimmer":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyBrightnessL2"] = True
                            else:
                                values_dict["zigbeePropertyBrightnessL2"] = False
                    case "brightness_l3":
                        if type_id == "multiDimmer":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyBrightnessL3"] = True
                            else:
                                values_dict["zigbeePropertyBrightnessL3"] = False

                    case "action":
                        if dev.deviceTypeId == "button":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyAction"] = True
                            else:
                                values_dict["zigbeePropertyAction"] = False
                        elif dev.deviceTypeId == "remoteAudio":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyRemoteAudio"] = True
                            else:
                                values_dict["zigbeePropertyRemoteAudio"] = False
                        elif dev.deviceTypeId == "remoteDimmer":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyRemoteDimmer"] = True
                            else:
                                values_dict["zigbeePropertyRemoteDimmer"] = False
                        elif dev.deviceTypeId == "sceneRotary":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertySceneRotary"] = True
                            else:
                                values_dict["zigbeePropertySceneRotary"] = False
                        if dev.deviceTypeId == "multiSwitch":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyMultiSwitchAction"] = True
                            else:
                                values_dict["zigbeePropertyMultiSwitchAction"] = False
                        if dev.deviceTypeId == "switch":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertySwitchAction"] = True
                            else:
                                values_dict["zigbeePropertySwitchAction"] = False
                        # elif dev.deviceTypeId == "vibrationSensor":
                        #     if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                        #         values_dict["zigbeePropertyVibrationAction"] = True
                        #     else:
                        #         values_dict["zigbeePropertyVibrationAction"] = False

                    case "angle" | "angle_x" | "angle_x_absolute" | "angle_y" | "angle_y_absolute" | "angle_z":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["rotations"]:
                            values_dict["zigbeePropertyAngles"] = True
                        else:
                            values_dict["zigbeePropertyAngles"] = False

                    case("action_rotation_angle" | "action_rotation_angle_speed" | "action_rotation_percent" |
                         "action_rotation_percent_speed" | "action_rotation_time"):
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES["rotations"]:
                            values_dict["zigbeePropertyRotations"] = True
                        else:
                            values_dict["zigbeePropertyRotations"] = False

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
                        # zigbee_device_property = "energy"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyEnergy"] = True
                        else:
                            values_dict["zigbeePropertyEnergy"] = False

                    case "humidity":
                        # zigbee_device_property = "humidity"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyHumidity"] = True
                        else:
                            values_dict["zigbeePropertyHumidity"] = False

                    case "illuminance" | "illuminance_lux":
                        # zigbee_device_property = "illuminance"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES.get(zigbee_device_property, ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES.get("illuminance", [])):
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
                        if type_id == "multiDimmer" or  type_id == "multiOutlet":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateL1"] = True
                            else:
                                values_dict["zigbeePropertyStateL1"] = False
                    case "state_l2":
                        if type_id == "multiDimmer" or type_id == "multiOutlet":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateL2"] = True
                            else:
                                values_dict["zigbeePropertyStateL2"] = False
                    case "state_l3":
                        if type_id == "multiDimmer" or type_id == "multiOutlet":
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
                        elif type_id == "multiSwitch":
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
                        elif type_id == "multiSwitch":
                            if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                values_dict["zigbeePropertyStateRight"] = True
                            else:
                                values_dict["zigbeePropertyStateRight"] = False

                    case "power":
                        # zigbee_device_property = "power"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPower"] = True
                        else:
                            values_dict["zigbeePropertyPower"] = False

                    case "power_left":
                        # zigbee_device_property = "power_left"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPowerLeft"] = True
                        else:
                            values_dict["zigbeePropertyPowerLeft"] = False

                    case "power_right":
                        # zigbee_device_property = "power_right"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPowerRight"] = True
                        else:
                            values_dict["zigbeePropertyPowerRight"] = False

                    case "presence_detection_options":
                        # zigbee_device_property = "presenceDetectionOptions"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPresenceDetectionOptions"] = True
                        else:
                            values_dict["zigbeePropertyPresenceDetectionOptions"] = False

                    case "pir_detection":
                        # zigbee_device_property = "pirDetection"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPirDetection"] = True
                        else:
                            values_dict["zigbeePropertyPirDetection"] = False

                    case "presence":
                        # zigbee_device_property = "presence"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyPresence"] = True
                            if type_id == "radarSensor":
                                values_dict["uspPresence"] = True
                                values_dict["uspPresenceIndigo"] = INDIGO_PRIMARY_DEVICE_MAIN_UI_STATE
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

                    case "strength":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyStrength"] = True
                        else:
                            values_dict["zigbeePropertyStrength"] = False

                    case "tamper":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyTamper"] = True
                        else:
                            values_dict["zigbeePropertyTamper"] = False

                    case "target_distance":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES.get("target_distance", []):
                            values_dict["zigbeePropertyTargetDistance"] = True
                        else:
                            values_dict["zigbeePropertyTargetDistance"] = False

                    case "temperature" | "device_temperature":
                        # zigbee_device_property = "temperature"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES.get(zigbee_device_property, ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES.get("temperature", [])):
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
                        # zigbee_device_property = "voltage"
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyVoltage"] = True
                        else:
                            values_dict["zigbeePropertyVoltage"] = False

                    case "water_leak":
                        if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                            values_dict["zigbeePropertyWaterLeak"] = True
                        else:
                            values_dict["zigbeePropertyWaterLeak"] = False

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
                            case "switch":
                                if type_id in ZD_PROPERTIES_SUPPORTED_BY_DEVICE_TYPES[zigbee_device_property]:
                                    values_dict["zigbeePropertyStateSingle"] = True
                                else:
                                    values_dict["zigbeePropertyStateSingle"] = False

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
