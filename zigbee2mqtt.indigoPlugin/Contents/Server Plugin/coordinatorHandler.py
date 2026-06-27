#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023
#

try:
    # noinspection PyUnresolvedReferences
    import indigo
except ImportError:
    pass

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    pass

# try:
#     import paho.mqtt.client as mqtt
# except ImportError:
#     pass

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.enums import CallbackAPIVersion
except ImportError:
    pass

import sys
import threading
import traceback
import time

from constants import *


# https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet
def decode(key, encrypted_password):
    # print(f"Python 3 Decode, Arguments: Key='{key}', Encrypted Password='{encrypted_password}'")

    f = Fernet(key)
    unencrypted_password = f.decrypt(encrypted_password)

    # print(f"Python 3 Decode: Unencrypted Password = {unencrypted_password}")

    return unencrypted_password


# noinspection PyPep8Naming
class ThreadCoordinatorHandler(threading.Thread):

    # This class handles interactions with the MQTT Broker

    def __init__(self, pluginGlobals, event, zc_dev_id):
        try:

            threading.Thread.__init__(self)

            self.globals = pluginGlobals

            self.mqtt_client = None

            self.zc_dev_id = zc_dev_id

            self.mqttHandlerLogger = logging.getLogger("Plugin.Zigbee2mqtt.MQTT")

            self.threadStop = event

            self.bad_disconnection = False

            self.mqtt_message_sequence = 0
            
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
        self.mqttHandlerLogger.error(log_message)

    def run(self):
        try:
            # Initialise routine on thread start

            zc_dev = indigo.devices[self.zc_dev_id]
            zc_dev.updateStateOnServer(key="status", value="disconnected")
            zc_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

            if self.globals[DEBUG]: self.mqttHandlerLogger.info(f"Client ID: {self.globals[ZC][self.zc_dev_id][MQTT_CLIENT_ID]}")

            self.mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2,
                                           client_id=self.globals[ZC][self.zc_dev_id][MQTT_CLIENT_ID],
                                           clean_session=True,
                                           userdata=None,
                                           protocol=self.globals[ZC][self.zc_dev_id][MQTT_PROTOCOL])

            # self.client = mqtt.Client(client_id=f"indigo-mqtt-{device.id}", clean_session=True, userdata=None, protocol=self.protocol, transport=self.transport)  # Example from @FlyingDiver

            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_disconnect = self.on_disconnect
            self.mqtt_client.on_subscribe = self.on_subscribe

            self.mqtt_client.reconnect_delay_set(min_delay=1, max_delay=60)

            # self.globals[ZC][self.zc_dev_id][MQTT_ROOT_TOPIC] = MQTT_ROOT_TOPIC_VALUE  # TODO: Get from Device Config - already setup by close device configui?
            mqtt_subscription = f"{self.globals[ZC][self.zc_dev_id][MQTT_ROOT_TOPIC]}/#"
            self.mqtt_client.message_callback_add(mqtt_subscription, self.handle_message)

            mqtt_connected = False
            try:
                broker_name = indigo.devices[self.zc_dev_id].name
                # self.mqttHandlerLogger.warning(f"Connect to {broker_name} [1] - User : {self.globals[ZC][self.mqtt_broker_dev_id][MQTT_USERNAME]}")
                decoded_password = ""
                if self.globals[ZC][self.zc_dev_id][MQTT_PASSWORD] != "":
                    encrypted_password = self.globals[ZC][self.zc_dev_id][MQTT_PASSWORD].encode()
                    # self.mqttHandlerLogger.warning(f"Connect to {broker_name} [2] - Encrypted Password [{type(encrypted_password)}]: '{encrypted_password}'")
                    decoded_password = decode(self.globals[ZC][self.zc_dev_id][MQTT_ENCRYPTION_KEY], encrypted_password)
                    # self.mqttHandlerLogger.warning(f"Connect to {broker_name} [3] - Decoded Password [{type(decoded_password)}]: '{decoded_password}'")

                if decoded_password != "" or self.globals[ZC][self.zc_dev_id][MQTT_USERNAME] != "":
                    self.mqtt_client.username_pw_set(username=self.globals[ZC][self.zc_dev_id][MQTT_USERNAME],
                                                     password=decoded_password)

                self.mqtt_client.connect(host=self.globals[ZC][self.zc_dev_id][MQTT_IP],
                                         port=self.globals[ZC][self.zc_dev_id][MQTT_PORT],
                                         keepalive=60,
                                         bind_address="")
                mqtt_connected = True
            except Exception as exception_error:
                # TODO: Make this more user friendly!
                self.mqttHandlerLogger.error(
                    f"Plugin is unable to connect to the Zigbee2mqtt MQTT Broker at {self.globals[ZC][self.zc_dev_id][MQTT_IP]}:{self.globals[ZC][self.zc_dev_id][MQTT_PORT]}. Is it running? Connection error reported as '{exception_error}'")
                self.exception_handler(exception_error, True)  # Log error and display failing statement

            if mqtt_connected:
                self.globals[ZC][self.zc_dev_id][MQTT_CLIENT] = self.mqtt_client

                self.mqtt_client.loop_start()

                while not self.threadStop.is_set():
                    # Interruptible wait so shutdown is immediate; interval long enough
                    # for paho's internal reconnect to run, short enough to catch a wedge.
                    if self.threadStop.wait(10):
                        break
                    try:
                        if not self.mqtt_client.is_connected():
                            self.mqttHandlerLogger.warning(
                                f"MQTT supervisor: broker appears disconnected — forcing reconnect to "
                                f"{self.globals[ZC][self.zc_dev_id][MQTT_IP]}:{self.globals[ZC][self.zc_dev_id][MQTT_PORT]}")
                            try:
                                self.mqtt_client.reconnect()
                            except Exception as supervisor_error:
                                self.mqttHandlerLogger.warning(
                                    f"MQTT supervisor: reconnect attempt failed: {supervisor_error} — will retry")
                    except Exception as supervisor_error:
                        self.mqttHandlerLogger.warning(
                            f"MQTT supervisor: health-check error: {supervisor_error} — will retry")
            else:
                pass
                # TODO: At this point, queue a recovery for n seconds time
                # TODO: In the meanwhile, just disable and then enable the Indigo Coordinator device

            self.handle_quit()

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def on_publish(self, client, userdata, mid):  # noqa [parameter value is not used]
        try:
            pass
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def on_connect(self, client, userdata, connect_flags, reason_code, properties):  # noqa [Unused parameter values]
        try:

            subscription_topic = f"{self.globals[ZC][self.zc_dev_id][MQTT_ROOT_TOPIC]}/#"
            if self.globals[DEBUG]: self.mqttHandlerLogger.warning(f"ZIGBEE2MQTT: Subscription Topic={subscription_topic}")
            self.mqtt_client.subscribe(subscription_topic, qos=1)

            self.globals[ZC][self.zc_dev_id][MQTT_CONNECTED] = True
            zc_dev = indigo.devices[self.zc_dev_id]
            zc_dev.updateStateOnServer(key="status", value="connected")
            zc_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)

            if self.bad_disconnection:  # Check if previous disconnection was bad to set as "reconnected" as opposed to "connected"
                self.bad_disconnection = False
                connection_ui = "Reconnected"
            else:
                connection_ui = "Connected"
            self.mqttHandlerLogger.info(f"{connection_ui} to Zigbee2mqtt MQTT Broker at {self.globals[ZC][self.zc_dev_id][MQTT_IP]}:{self.globals[ZC][self.zc_dev_id][MQTT_PORT]}")

            for zigbee_coordinator_ieee in self.globals[ZD]:
                for zigbee_device_ieee in self.globals[ZD][zigbee_coordinator_ieee]:
                    self.globals[ZD][zigbee_coordinator_ieee][zigbee_device_ieee][ZD_MESSAGE_COUNT] = 0

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):  # noqa [Unused parameter values]
        try:
            self.globals[ZC][self.zc_dev_id][MQTT_CONNECTED] = False
            if reason_code.is_failure:
                self.mqttHandlerLogger.warning(
                    f"Unexpected disconnection from Zigbee2mqtt MQTT Broker at "
                    f"{self.globals[ZC][self.zc_dev_id][MQTT_IP]}:{self.globals[ZC][self.zc_dev_id][MQTT_PORT]} "
                    f"[Code {reason_code.value} - {reason_code}]. Supervisor will attempt to reconnect.")
                self.bad_disconnection = True
            else:
                self.mqttHandlerLogger.info(f"Disconnected from Zigbee2mqtt MQTT Broker at {self.globals[ZC][self.zc_dev_id][MQTT_IP]}:{self.globals[ZC][self.zc_dev_id][MQTT_PORT]}")
                self.mqtt_client.loop_stop()

            zc_dev = indigo.devices[self.zc_dev_id]
            zc_dev.updateStateOnServer(key="status", value="disconnected")
            zc_dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def handle_quit(self):
        try:
            self.mqtt_client.disconnect()
            self.mqtt_client.loop_stop()
            # self.mqttHandlerLogger.info(f"Disconnected from Zigbee2mqtt MQTT Broker at {self.globals[ZC][self.zc_dev_id][MQTT_IP]}:{self.globals[ZC][self.zc_dev_id][MQTT_PORT]}")
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def on_subscribe(self, client, userdata, mid, reason_code_list, properties):  # noqa [Unused parameter values]
        try:
            pass
        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement

    def handle_message(self, client, userdata, msg):  # noqa [Unused parameter values: client, userdata]
        try:
            self.mqtt_message_sequence += 1
            topic_list = msg.topic.split("/")  # noqa [Duplicated code fragment!]
            payload = msg.payload.decode('utf-8')

            if len(topic_list) < 2:
                return

            if topic_list[0] == self.globals[ZC][self.zc_dev_id][MQTT_ROOT_TOPIC]:  # e.g: "zigbee2mqtt"
                # self.mqttHandlerLogger.warning(f"ZIGBEE2MQTT-2 [{self.mqtt_message_sequence}]: Topic={msg.topic}, Payload={msg.payload}")
                # self.mqttHandlerLogger.warning(f"QUEUEING [{self.mqtt_message_sequence}]: Topic={msg.topic}")

                if topic_list[1] == "bridge":
                    zigbee_process_command = HANDLE_ZIGBEE_COORDINATOR_MQTT_TOPIC
                elif topic_list[1] in self.globals[ZG][indigo.devices[self.zc_dev_id].address]:
                    zigbee_process_command = HANDLE_ZIGBEE_GROUP_MQTT_TOPIC
                else:
                    zigbee_process_command = HANDLE_ZIGBEE_DEVICE_MQTT_TOPIC

                self.globals[QUEUES][MQTT_ZIGBEE2MQTT_QUEUE][self.zc_dev_id].put([self.mqtt_message_sequence, zigbee_process_command, self.zc_dev_id, msg.topic, topic_list, payload])

        except Exception as exception_error:
            self.exception_handler(exception_error, True)  # Log error and display failing statement
