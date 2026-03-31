#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# MQTT-related methods extracted from plugin.py

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

from constants import (
    MQTT_CLIENT,
    MQTT_FILTERS,
    ZC,
    ZD,
    ZD_FRIENDLY_NAME,
)


class MQTTMixin:
    """Mixin class containing MQTT publishing and filtering methods."""

    def mqtt_list_zigbee_devices(self, filter="", valuesDict=None, typeId="", targetId=0):  # noqa [parameter value is not used]
        try:
            zc_dev = indigo.devices[targetId]
            zigbee_coordinator_ieee = zc_dev.address

            zigbee_devices_list = list()

            # Entry split on triple | gives: option, zigbee_coordinator_ieee, None  | All | zigbee device friendly name
            zigbee_devices_list.append((f"0|||{zigbee_coordinator_ieee}|||-- Don't Log Any Devices --", "-- Don't Log Any Devices --"))
            zigbee_devices_list.append((f"1|||{zigbee_coordinator_ieee}|||-- Log All Devices --", "-- Log All Devices --"))

            for zigbee_device_ieee, zigbee_device_details in self.globals[ZD][zigbee_coordinator_ieee].items():
                # self.logger.warning(f"zigbee_device_ieee: {zigbee_device_ieee}")
                if zigbee_device_ieee[0:2] == "0x":
                    if ZD_FRIENDLY_NAME in self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee]:
                        zigbee_device_friendly_name = self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_FRIENDLY_NAME]
                        zigbee_devices_list.append((f"2|||{zigbee_coordinator_ieee}|||{zigbee_device_friendly_name}", f"{zigbee_device_friendly_name}"))
                    else:
                        self.logger.warning(f"mqtt_list_zigbee_devices: Friendly name missing for zigbee device with address: {zigbee_device_ieee}")
            return sorted(zigbee_devices_list, key=lambda name: name[1].lower())  # sort by Zigbee device friendly name

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def publish_zigbee_topic(self, zigbee_coordinator_ieee, friendly_name, topic, payload):
        try:
            # TODO: Check if self.globals[ZC][MQTT_CONNECTED]

            published = False
            for zc_dev_id, zc_dev_details in self.globals[ZC].items():
                # self.globals[ZC][coordinator_dev.id][ZC_IEEE]
                zc_dev = indigo.devices[zc_dev_id]
                if zc_dev.address == zigbee_coordinator_ieee:
                    # if self.globals[ZC][mqtt_broker_device_id][MQTT_PUBLISH_TO_HOMIE]:
                    # topic = "zigbee2mqtt/Outlet 1/set"
                    self.globals[ZC][zc_dev_id][MQTT_CLIENT].publish(topic, payload)
                    published = True
                    # if self.globals[DEBUG]:

            if published:
                self.mqtt_filter_log_processing(zc_dev.name, zigbee_coordinator_ieee, friendly_name, topic, payload)  # noqa

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def mqtt_filter_log_processing(self, zc_dev_name, zigbee_coordinator_ieee, topic_friendly_name, topics, payload):
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
                self.logger.warning(f">>> Published to '{zc_dev_name}': Topic='{topics}', Payload='{payload}'")  # noqa [unresolved attribute reference]

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
