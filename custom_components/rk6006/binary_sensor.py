"""Binary sensor platform for RK6006."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import RK6006Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RK6006 binary sensor platform."""
    coordinator: RK6006Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            RK6006CVModeBinarySensor(coordinator),
            RK6006CCModeBinarySensor(coordinator),
            RK6006OVPBinarySensor(coordinator),
            RK6006OCPBinarySensor(coordinator),
        ]
    )


class RK6006CVModeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for CV (Constant Voltage) mode."""

    _attr_icon = "mdi:current-dc"
    _attr_device_class = None

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_cv_mode"
        self._attr_name = "RK6006 CV Mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool:
        """Return True if in CV (Constant Voltage) mode."""
        return self.coordinator.data.get("output_mode") == "CV"


class RK6006CCModeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for CC (Constant Current) mode."""

    _attr_icon = "mdi:current-ac"
    _attr_device_class = None

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_cc_mode"
        self._attr_name = "RK6006 CC Mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool:
        """Return True if in CC (Constant Current) mode."""
        return self.coordinator.data.get("output_mode") == "CC"


class RK6006OVPBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for OVP (Over Voltage Protection) trigger."""

    _attr_icon = "mdi:flash-alert"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_ovp_triggered"
        self._attr_name = "RK6006 OVP Triggered"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool:
        """Return True if OVP is triggered."""
        return self.coordinator.data.get("ovp_triggered", False)


class RK6006OCPBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for OCP (Over Current Protection) trigger."""

    _attr_icon = "mdi:flash-alert"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_ocp_triggered"
        self._attr_name = "RK6006 OCP Triggered"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool:
        """Return True if OCP is triggered."""
        return self.coordinator.data.get("ocp_triggered", False)
