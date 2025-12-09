"""Switch platform for RK6006 Power Supply."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up RK6006 switch."""
    coordinator: RK6006Coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        RK6006OutputSwitch(coordinator),
        RK6006ConnectionSwitch(coordinator),
        RK6006BuzzerSwitch(coordinator),
        RK6006PowerOnBootSwitch(coordinator),
        RK6006TakeOutSwitch(coordinator),
    ])


class RK6006OutputSwitch(CoordinatorEntity, SwitchEntity):
    """Output switch entity."""

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 Output"
        self._attr_unique_id = f"{coordinator.address}_output"
        self._attr_icon = "mdi:power"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool:
        """Return true if output is on."""
        return self.coordinator.data.get("output_enabled", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the output on."""
        await self.coordinator.async_set_output(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the output off."""
        await self.coordinator.async_set_output(False)


class RK6006ConnectionSwitch(CoordinatorEntity, SwitchEntity):
    """Connection control switch entity."""
    
    # Override to prevent CoordinatorEntity from making us unavailable
    _attr_available = True

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 Connection"
        self._attr_unique_id = f"{coordinator.address}_connection"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def available(self) -> bool:
        """Return True - connection switch is always available."""
        return True
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        # Force initial state update even if coordinator is unavailable
        self.async_write_ha_state()
    
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Always update state even when coordinator fails
        # This ensures the switch reflects the actual connection_enabled state
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if connection is enabled."""
        return self.coordinator.connection_enabled

    @property
    def icon(self) -> str:
        """Return icon based on state."""
        return "mdi:bluetooth-connect" if self.is_on else "mdi:bluetooth-off"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable connection."""
        await self.coordinator.async_enable_connection()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable connection."""
        await self.coordinator.async_disable_connection()
        self.async_write_ha_state()


class RK6006BuzzerSwitch(CoordinatorEntity, SwitchEntity):
    """Buzzer switch entity."""

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 Buzzer"
        self._attr_unique_id = f"{coordinator.address}_buzzer"
        self._attr_icon = "mdi:volume-high"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool:
        """Return true if buzzer is enabled."""
        return self.coordinator.data.get("buzzer", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable buzzer."""
        await self.coordinator.async_set_buzzer(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable buzzer."""
        await self.coordinator.async_set_buzzer(False)


class RK6006PowerOnBootSwitch(CoordinatorEntity, SwitchEntity):
    """Power on boot switch entity."""

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 Power On Boot"
        self._attr_unique_id = f"{coordinator.address}_power_on_boot"
        self._attr_icon = "mdi:power-plug"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool:
        """Return true if power on boot is enabled."""
        return self.coordinator.data.get("power_on_boot", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable power on boot."""
        await self.coordinator.async_set_power_on_boot(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable power on boot."""
        await self.coordinator.async_set_power_on_boot(False)


class RK6006TakeOutSwitch(CoordinatorEntity, SwitchEntity):
    """Take out switch entity."""

    def __init__(self, coordinator: RK6006Coordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "RK6006 Take Out"
        self._attr_unique_id = f"{coordinator.address}_take_out"
        self._attr_icon = "mdi:tray-arrow-up"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": "RK6006 Power Supply",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def is_on(self) -> bool:
        """Return true if take out is enabled."""
        return self.coordinator.data.get("take_out", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable take out."""
        await self.coordinator.async_set_take_out(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable take out."""
        await self.coordinator.async_set_take_out(False)
