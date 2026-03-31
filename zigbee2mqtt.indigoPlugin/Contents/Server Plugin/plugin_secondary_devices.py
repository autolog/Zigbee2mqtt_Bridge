#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Secondary device management methods extracted from plugin.py

from datetime import datetime

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import (
    INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE,
    INDIGO_SECONDARY_DEVICE,
    INDIGO_SUB_TYPE_INFO,
    INDIGO_SUPPORTED_SUB_TYPES_BY_DEVICE,
)


class SecondaryDevicesMixin:
    """Mixin class containing secondary device management methods."""

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
            elif dev.deviceTypeId == "illuminanceSensor" or dev.deviceTypeId == "illuminanceSensorSecondary":
                if dev.subType != indigo.kSensorDeviceSubType.Illuminance:
                    dev.subType = indigo.kSensorDeviceSubType.Illuminance
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "multiDimmer" or dev.deviceTypeId == "multiDimmerSecondary2" or dev.deviceTypeId == "multiDimmerSecondary3":
                if dev.subType != indigo.kDimmerDeviceSubType.Dimmer:
                    dev.subType = indigo.kDimmerDeviceSubType.Dimmer
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "multiOutlet" or dev.deviceTypeId == "multiOutletSecondary2" or dev.deviceTypeId == "multiOutletSecondary3" or dev.deviceTypeId == "multiOutletSecondary4" or dev.deviceTypeId == "multiOutletSecondary5":
                if dev.subType != indigo.kRelayDeviceSubType.Outlet:
                    dev.subType = indigo.kRelayDeviceSubType.Outlet
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "multiSocket" or dev.deviceTypeId == "multiSocketSecondary":
                if dev.subType != indigo.kRelayDeviceSubType.Outlet:
                    dev.subType = indigo.kRelayDeviceSubType.Outlet
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "multiSwitch":
                if dev.subType != indigo.kDeviceSubType.Other:
                    dev.subType = indigo.kDeviceSubType.Other + ",ui=Scene"
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "multiSwitchSecondaryLeft":
                if dev.subType != indigo.kRelayDeviceSubType.Switch:
                    dev.subType = indigo.kRelayDeviceSubType.Switch + ",ui=Switch Left"
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "multiSwitchSecondaryRight":
                if dev.subType != indigo.kRelayDeviceSubType.Switch:
                    dev.subType = indigo.kRelayDeviceSubType.Switch + ",ui=Switch Right"
                    dev.replaceOnServer()

            elif dev.deviceTypeId == "motionSensor" or dev.deviceTypeId == "multiSensor" or dev.deviceTypeId == "motionSensorSecondary":
                if dev.subType != indigo.kSensorDeviceSubType.Motion:
                    dev.subType = indigo.kSensorDeviceSubType.Motion
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "outlet":
                if dev.subType != indigo.kRelayDeviceSubType.Outlet:
                    dev.subType = indigo.kRelayDeviceSubType.Outlet
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "presenceSensor" or dev.deviceTypeId == "radarSensor":
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
            elif dev.deviceTypeId == "switch":
                if dev.subType != indigo.kDeviceSubType.Other:
                    dev.subType = indigo.kDeviceSubType.Other + ",ui=Scene"
                    dev.replaceOnServer()
            elif dev.deviceTypeId == "switchSecondarySingle":
                if dev.subType != indigo.kRelayDeviceSubType.Switch:
                    dev.subType = indigo.kRelayDeviceSubType.Switch + ",ui=Switch"
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
                    case "multiDimmerSecondary2":
                        primary_props["secondaryDeviceMultiDimmer2"] = 0
                    case "multiDimmerSecondary3":
                        primary_props["secondaryDeviceMultiDimmer3"] = 0
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
                    case "multiSwitchSecondaryLeft":
                        primary_props["secondaryDeviceMultiSwitchLeft"] = 0
                    case "multiSwitchSecondaryRight":
                        primary_props["secondaryDeviceMultiSwitchRight"] = 0
                    case "switchSecondarySingle":
                        primary_props["secondaryDeviceSwitchSingle"] = 0
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
                                                                            # TODO:   WORKED ROUND THIS FOR MULTI_DIMMER & MULTI-OUTLET BY HAVING DIFFERENT SECONDARY DEVICE TYPES
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
                    case "multiODimmerSecondary2":
                        primary_props["secondaryDeviceMultiDimmert2"] = secondary_dev_id
                    case "multiODimmerSecondary3":
                        primary_props["secondaryDeviceMultiDimmert3"] = secondary_dev_id
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
                    case "multiSwitchSecondaryLeft":
                        primary_props["secondaryDeviceMultiSwitchLeft"] = secondary_dev_id
                    case "multiSwitchSecondaryRight":
                        primary_props["secondaryDeviceMultiSwitchRight"] = secondary_dev_id
                    case"switchSecondarySingle":
                        primary_props["secondaryDeviceSwitchSingle"] = secondary_dev_id
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
                    # TODO: Differentiate for Outlet devices L1 thru L5 + Dimmer devices L1 thru L3
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
