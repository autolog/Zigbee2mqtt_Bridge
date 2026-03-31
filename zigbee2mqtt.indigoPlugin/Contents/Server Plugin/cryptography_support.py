#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Cryptography support functions for password encoding/decoding

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from constants import MQTT_ENCRYPTION_PASSWORD_PYTHON_3


# https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password/66728699#66728699

def encode(unencrypted_password):
    internal_password = MQTT_ENCRYPTION_PASSWORD_PYTHON_3  # Byte string

    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    key = base64.urlsafe_b64encode(kdf.derive(internal_password))

    f = Fernet(key)

    unencrypted_password = unencrypted_password.encode()  # str -> b
    encrypted_password = f.encrypt(unencrypted_password)

    return key, encrypted_password


def decode(key, encrypted_password):
    f = Fernet(key)
    unencrypted_password = f.decrypt(encrypted_password)

    return unencrypted_password
