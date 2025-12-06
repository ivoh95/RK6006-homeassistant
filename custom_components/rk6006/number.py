"""Number platform for RK6006 Power Supply."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
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
    """Set up RK6006 numbers."""
    coordinator: RK6006Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            RK6006VoltageNumber(coordinator),
            RK6006CurrentNumber(coordinator),
            RK6006OVPNumber(coordinator),
            RK6006OCPNumber(coordinator),
            RK6006BacklightNumber(coordinator),
        ]
    )


class RK6006VoltageNumber(CoordinatorEntity, NumberEntity):
    """Voltage setpoint number entity."""

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 Voltage Setpoint"
        self._attr_unique_id = f"{coordinator.address}_voltage_set"
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 60
        self._attr_native_step = 0.01
        self._attr_mode = NumberMode.BOX
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.coordinator.data.get("voltage_set", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.async_set_voltage(value)


class RK6006CurrentNumber(CoordinatorEntity, NumberEntity):
    """Current setpoint number entity."""

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 Current Setpoint"
        self._attr_unique_id = f"{coordinator.address}_current_set"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_icon = "mdi:current-dc"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 6
        self._attr_native_step = 0.001
        self._attr_mode = NumberMode.BOX
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.coordinator.data.get("current_set", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.async_set_current(value)


class RK6006OVPNumber(CoordinatorEntity, NumberEntity):
    """Over-voltage protection number entity."""

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 OVP"
        self._attr_unique_id = f"{coordinator.address}_ovp"
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_native_min_value = 0
        self._attr_native_max_value = 65
        self._attr_native_step = 0.01
        self._attr_mode = NumberMode.BOX
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.coordinator.data.get("ovp", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.async_set_ovp(value)


class RK6006OCPNumber(CoordinatorEntity, NumberEntity):
    """Over-current protection number entity."""

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 OCP"
        self._attr_unique_id = f"{coordinator.address}_ocp"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_native_min_value = 0
        self._attr_native_max_value = 6.2
        self._attr_native_step = 0.001
        self._attr_mode = NumberMode.BOX
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def native_value(self) -> float:
        """Return the current value."""
        return self.coordinator.data.get("ocp", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.async_set_ocp(value)


class RK6006BacklightNumber(CoordinatorEntity, NumberEntity):
    """Backlight number entity."""

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 Backlight"
        self._attr_unique_id = f"{coordinator.address}_backlight"
        self._attr_icon = "mdi:brightness-6"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 5
        self._attr_native_step = 1
        self._attr_mode = NumberMode.SLIDER
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def native_value(self) -> int:
        """Return the current value."""
        return self.coordinator.data.get("backlight", 5)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.async_set_backlight(int(value))
