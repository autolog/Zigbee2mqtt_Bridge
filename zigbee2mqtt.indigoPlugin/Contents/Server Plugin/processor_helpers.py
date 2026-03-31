#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Processor helper methods extracted from zigbeeHandler.py

from __future__ import annotations

from typing import Any, Optional, Tuple, Union

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import (
    DEBUG,
    INDIGO_ONE_SPACE_BEFORE_UNITS,
    INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE,
    INDIGO_SECONDARY_DEVICE,
    MQTT_FILTERS,
)


class SecondaryDeviceResult:
    """Result object for resolve_secondary_device helper."""
    __slots__ = ('device', 'state_key', 'is_secondary', 'is_valid')

    device: Any  # indigo.Device
    state_key: str
    is_secondary: bool
    is_valid: bool

    def __init__(self, device: Any, state_key: str, is_secondary: bool, is_valid: bool) -> None:
        self.device = device
        self.state_key = state_key
        self.is_secondary = is_secondary
        self.is_valid = is_valid


class ProcessorHelpersMixin:
    """Mixin class containing processor utility methods."""

    def resolve_secondary_device(self, zd_dev: Any, property_name: str,
                                  secondary_dev_prop_key: str, primary_state_key: str) -> SecondaryDeviceResult:
        """
        Resolve whether to use primary or secondary device for a sensor property.

        Args:
            zd_dev: The primary Zigbee device
            property_name: Property name for pluginProps lookup (e.g., "Humidity", "Temperature")
            secondary_dev_prop_key: Plugin prop key for secondary device ID (e.g., "secondaryDeviceHumiditySensor")
            primary_state_key: State key for primary device (e.g., "humidity", "temperature")

        Returns:
            SecondaryDeviceResult with:
                - device: The device to update (primary or secondary)
                - state_key: The state key to update ("sensorValue" for secondary, primary_state_key for primary)
                - is_secondary: True if using secondary device
                - is_valid: False if secondary device was expected but not found
        """
        try:
            indigo_prop = zd_dev.pluginProps.get(f"usp{property_name}Indigo", INDIGO_PRIMARY_DEVICE_ADDITIONAL_STATE)
            device_to_process = zd_dev
            is_secondary = False
            state_key = primary_state_key

            secondary_dev_id = zd_dev.pluginProps.get(secondary_dev_prop_key, 0)

            if indigo_prop == INDIGO_SECONDARY_DEVICE and secondary_dev_id != 0:
                if secondary_dev_id in indigo.devices:
                    device_to_process = indigo.devices[secondary_dev_id]
                    is_secondary = True
                    state_key = "sensorValue"
                else:
                    # Secondary device expected but not found
                    return SecondaryDeviceResult(zd_dev, state_key, False, False)

            # Check if secondary was expected but no device ID was configured
            if indigo_prop == INDIGO_SECONDARY_DEVICE and not is_secondary:
                return SecondaryDeviceResult(zd_dev, state_key, False, False)

            return SecondaryDeviceResult(device_to_process, state_key, is_secondary, True)

        except Exception as exception_error:
            self.exception_handler(exception_error, True)
            return SecondaryDeviceResult(zd_dev, primary_state_key, False, False)

    def update_state_if_changed(self, target_device: Any, state_key: str,
                                 new_value: Union[int, float], ui_value: str,
                                 primary_device: Any, hide_broadcast_prop: str, property_label: str,
                                 state_image: Optional[Any] = None,
                                 compare_value: Optional[Union[int, float]] = None) -> bool:
        """
        Update a device state if the value has changed, with optional logging.

        Args:
            target_device: The Indigo device to update
            state_key: The state key to update (e.g., "humidity", "sensorValue")
            new_value: The new value to set (already formatted)
            ui_value: The UI display value string
            primary_device: The primary device (for reading pluginProps)
            hide_broadcast_prop: Plugin prop key for hiding broadcast (e.g., "hideHumidityBroadcast")
            property_label: Human-readable label for logging (e.g., "humidity level")
            state_image: Optional indigo.kStateImageSel value to set on change
            compare_value: Optional value to compare against (if different from new_value)

        Returns:
            True if state was updated, False if unchanged
        """
        try:
            # Use compare_value if provided, otherwise use new_value for comparison
            value_to_compare = compare_value if compare_value is not None else new_value

            if target_device.states[state_key] != value_to_compare:
                # State changed - update it
                if state_image is not None:
                    target_device.updateStateImageOnServer(state_image)
                self.key_value_lists[target_device.id].append({
                    'key': state_key,
                    'value': new_value,
                    'uiValue': ui_value
                })
                if not bool(primary_device.pluginProps.get(hide_broadcast_prop, False)):
                    self.zigbeeLogger.info(f"received \"{target_device.name}\" {property_label} {ui_value}")
                return True
            else:
                # State unchanged - only log in debug mode
                if not bool(primary_device.pluginProps.get(hide_broadcast_prop, False)):
                    if self.globals[DEBUG]:
                        self.zigbeeLogger.info(f"received \"{target_device.name}\" unchanged {property_label} {ui_value}")
                return False

        except Exception as exception_error:
            self.exception_handler(exception_error, True)
            return False

    def append_state_update(self, device_id: int, state_key: str,
                             value: Any, ui_value: Optional[str] = None) -> None:
        """
        Simple helper to append a state update to key_value_lists.

        Args:
            device_id: The Indigo device ID
            state_key: The state key to update
            value: The value to set
            ui_value: Optional UI display value
        """
        update: dict[str, Any] = {'key': state_key, 'value': value}
        if ui_value is not None:
            update['uiValue'] = ui_value
        self.key_value_lists[device_id].append(update)

    def determine_secondary_device_id(self, dev_id: int, secondary_dev_type_id: str) -> int:
        try:
            # TODO: Use links stored in Primary
            dev_id_list = indigo.device.getGroupList(dev_id)
            secondary_dev_id: int = 0
            if len(dev_id_list) > 1:
                for grouped_dev_id in dev_id_list:
                    if grouped_dev_id != dev_id and indigo.devices[grouped_dev_id].deviceTypeId == secondary_dev_type_id:
                        secondary_dev_id = grouped_dev_id
                        break
            return secondary_dev_id

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
            return 0

    def processDecimalPlaces(self, field: Union[int, float], decimal_places: int,
                              units: str, space_before_units: bool) -> Tuple[Union[int, float], str]:
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
            return 0, ""

    def mqtt_filter_log_processing(self, zigbee_coordinator_ieee: str,
                                    topic_friendly_name: str, topics: str, payload: str) -> None:
        try:
            log_mqtt_msg: bool = False  # Assume MQTT message should NOT be logged

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
