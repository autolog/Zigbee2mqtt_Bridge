#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zigbee2mqtt - Plugin © Autolog 2023-2026
#
# Configuration validation helpers

from __future__ import annotations

from typing import Any, Optional, Tuple, Union


class ConfigValidationMixin:
    """Mixin class providing configuration validation helpers."""

    def get_int_config(self, props: dict, key: str, default: int = 0,
                       min_val: Optional[int] = None, max_val: Optional[int] = None,
                       device_name: str = "") -> int:
        """
        Safely get an integer configuration value with optional range validation.

        Args:
            props: Plugin properties dictionary
            key: Property key to retrieve
            default: Default value if key missing or invalid
            min_val: Optional minimum allowed value
            max_val: Optional maximum allowed value
            device_name: Device name for warning messages

        Returns:
            Validated integer value or default
        """
        try:
            raw_value = props.get(key, default)
            if raw_value is None or raw_value == "":
                return default

            value = int(raw_value)

            if min_val is not None and value < min_val:
                if device_name:
                    self.zigbeeLogger.warning(
                        f"Device '{device_name}': Config '{key}' value {value} below minimum {min_val}, using {min_val}.")
                value = min_val

            if max_val is not None and value > max_val:
                if device_name:
                    self.zigbeeLogger.warning(
                        f"Device '{device_name}': Config '{key}' value {value} above maximum {max_val}, using {max_val}.")
                value = max_val

            return value

        except (ValueError, TypeError):
            if device_name:
                self.zigbeeLogger.warning(
                    f"Device '{device_name}': Config '{key}' has invalid value '{props.get(key)}', using default {default}.")
            return default

    def get_float_config(self, props: dict, key: str, default: float = 0.0,
                         min_val: Optional[float] = None, max_val: Optional[float] = None,
                         device_name: str = "") -> float:
        """
        Safely get a float configuration value with optional range validation.

        Args:
            props: Plugin properties dictionary
            key: Property key to retrieve
            default: Default value if key missing or invalid
            min_val: Optional minimum allowed value
            max_val: Optional maximum allowed value
            device_name: Device name for warning messages

        Returns:
            Validated float value or default
        """
        try:
            raw_value = props.get(key, default)
            if raw_value is None or raw_value == "":
                return default

            value = float(raw_value)

            if min_val is not None and value < min_val:
                if device_name:
                    self.zigbeeLogger.warning(
                        f"Device '{device_name}': Config '{key}' value {value} below minimum {min_val}, using {min_val}.")
                value = min_val

            if max_val is not None and value > max_val:
                if device_name:
                    self.zigbeeLogger.warning(
                        f"Device '{device_name}': Config '{key}' value {value} above maximum {max_val}, using {max_val}.")
                value = max_val

            return value

        except (ValueError, TypeError):
            if device_name:
                self.zigbeeLogger.warning(
                    f"Device '{device_name}': Config '{key}' has invalid value '{props.get(key)}', using default {default}.")
            return default

    def get_decimal_places(self, props: dict, key: str, device_name: str = "") -> int:
        """
        Get decimal places configuration with validation (0-10 range).

        Args:
            props: Plugin properties dictionary
            key: Property key for decimal places setting
            device_name: Device name for warning messages

        Returns:
            Validated decimal places (0-10)
        """
        return self.get_int_config(props, key, default=0, min_val=0, max_val=10, device_name=device_name)

    def get_secondary_device_id(self, props: dict, key: str, device_name: str = "") -> int:
        """
        Get a secondary device ID with validation that it exists.

        Args:
            props: Plugin properties dictionary
            key: Property key for secondary device ID
            device_name: Primary device name for warning messages

        Returns:
            Valid device ID or 0 if invalid/not found
        """
        try:
            import indigo

            raw_value = props.get(key, 0)
            if raw_value is None or raw_value == "" or raw_value == 0:
                return 0

            device_id = int(raw_value)

            if device_id != 0 and device_id not in indigo.devices:
                if device_name:
                    self.zigbeeLogger.warning(
                        f"Device '{device_name}': Secondary device ID {device_id} ('{key}') no longer exists. Check device configuration.")
                return 0

            return device_id

        except (ValueError, TypeError):
            if device_name:
                self.zigbeeLogger.warning(
                    f"Device '{device_name}': Config '{key}' has invalid device ID '{props.get(key)}'.")
            return 0

    def validate_unit_string(self, props: dict, key: str, default: str = "",
                             allowed: Optional[list] = None, device_name: str = "") -> str:
        """
        Get a unit string configuration with optional validation against allowed values.

        Args:
            props: Plugin properties dictionary
            key: Property key for unit string
            default: Default value if key missing or invalid
            allowed: Optional list of allowed values
            device_name: Device name for warning messages

        Returns:
            Validated unit string or default
        """
        value = props.get(key, default)
        if value is None:
            return default

        value = str(value)

        if allowed is not None and value not in allowed:
            if device_name:
                self.zigbeeLogger.warning(
                    f"Device '{device_name}': Config '{key}' has unexpected value '{value}'. Expected one of: {allowed}.")
            # Don't override - user may have custom units

        return value

    def validate_temperature_conversion(self, props: dict, device_name: str = "") -> str:
        """
        Validate temperature unit conversion setting.

        Args:
            props: Plugin properties dictionary
            device_name: Device name for warning messages

        Returns:
            Valid conversion setting: "C", "F", "C>F", or "F>C"
        """
        valid_conversions = ["C", "F", "C>F", "F>C"]
        value = props.get("uspTemperatureUnitsConversion", "C")

        if value not in valid_conversions:
            if device_name:
                self.zigbeeLogger.warning(
                    f"Device '{device_name}': Invalid temperature conversion '{value}'. Using 'C'.")
            return "C"

        return value

    def validate_hysteresis(self, props: dict, key: str, default: float = 6.0,
                            device_name: str = "") -> float:
        """
        Validate hysteresis value (must be non-negative).

        Args:
            props: Plugin properties dictionary
            key: Property key for hysteresis setting
            default: Default hysteresis value
            device_name: Device name for warning messages

        Returns:
            Validated hysteresis value (>= 0)
        """
        return self.get_float_config(props, key, default=default, min_val=0.0, device_name=device_name)

    def validate_button_count(self, props: dict, device_name: str = "") -> int:
        """
        Validate number of buttons configuration.

        Args:
            props: Plugin properties dictionary
            device_name: Device name for warning messages

        Returns:
            Valid button count (1-20)
        """
        return self.get_int_config(props, "uspNumberOfButtons", default=1, min_val=1, max_val=20, device_name=device_name)
