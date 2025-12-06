"""Sensor platform for RK6006 Power Supply."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
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
    """Set up RK6006 sensors."""
    coordinator: RK6006Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            RK6006Sensor(coordinator, "voltage", "Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
            RK6006Sensor(coordinator, "current", "Current", UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT),
            RK6006Sensor(coordinator, "power", "Power", UnitOfPower.WATT, SensorDeviceClass.POWER),
            RK6006Sensor(coordinator, "input_voltage", "Input Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
            RK6006Sensor(coordinator, "temp_internal", "Internal Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
            RK6006Sensor(coordinator, "temp_external", "External Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
            RK6006Sensor(coordinator, "amp_hours", "Amp Hours", "Ah", None, SensorStateClass.TOTAL_INCREASING),
            RK6006Sensor(coordinator, "watt_hours", "Watt Hours", UnitOfEnergy.WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
            RK6006ProtectionSensor(coordinator),
        ]
    )


class RK6006Sensor(CoordinatorEntity, SensorEntity):
    """Representation of an RK6006 sensor."""

    def __init__(
        self,
        coordinator: RK6006Coordinator,
        key: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"RK6006 {name}"
        self._attr_unique_id = f"{coordinator.address}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }
        # Disable external temp sensor by default if no probe detected
        if key == "temp_external":
            self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._key)
        # Don't show external temp if no probe
        if self._key == "temp_external" and value is None:
            return None
        return value


class RK6006ProtectionSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing protection status."""

    _attr_icon = "mdi:shield-alert"

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 Protection Status"
        self._attr_unique_id = f"{coordinator.address}_protection_status"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def native_value(self):
        """Return the protection status."""
        status = self.coordinator.data.get("protection_status", "unknown")
        return status.upper()

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return {
            "ovp_triggered": self.coordinator.data.get("ovp_triggered", False),
            "ocp_triggered": self.coordinator.data.get("ocp_triggered", False),
        }
