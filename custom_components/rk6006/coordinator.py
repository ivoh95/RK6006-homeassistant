"""Coordinator for RK6006 Power Supply."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL, CONF_CONNECTION_ENABLED
from .rk6006 import RK6006

_LOGGER = logging.getLogger(__name__)


class RK6006Coordinator(DataUpdateCoordinator):
    """Class to manage fetching RK6006 data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.address = entry.data[CONF_ADDRESS]
        self.device = RK6006(self.address)
        self._connected = False
        # Read connection enabled state from config entry, default to True for backward compatibility
        self._connection_enabled = entry.data.get(CONF_CONNECTION_ENABLED, True)
        self._consecutive_errors = 0
        self._max_consecutive_errors = 3  # Allow 3 failures before marking unavailable
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Update data via library."""
        if not self._connection_enabled:
            # Connection is disabled, raise UpdateFailed to mark entities unavailable
            raise UpdateFailed("Connection is disabled")
        
        try:
            if not self._connected:
                _LOGGER.info("Connecting to RK6006 at %s", self.address)
                await self.device.connect()
                self._connected = True
                _LOGGER.info("Successfully connected to RK6006")
            
            # Fetch all data
            _LOGGER.debug("Fetching status data")
            status = await self.device.get_status()
            settings = await self.device.get_settings()
            temps = await self.device.get_temperature()
            input_v = await self.device.get_input_voltage()
            protection = await self.device.get_protection_settings()
            protection_status = await self.device.get_protection_status()
            energy = await self.device.get_energy_counters()
            backlight = await self.device.get_backlight()
            
            # Get output state and additional settings
            output_state = await self.device.read_register(self.device.REG_OUTPUT_STATE)
            output_mode = await self.device.get_output_mode()
            buzzer = await self.device.get_buzzer()
            power_on_boot = await self.device.get_power_on_boot()
            take_out = await self.device.get_take_out()
            
            # Reset error counter on success
            self._consecutive_errors = 0
            
            data = {
                "voltage": status["voltage"],
                "current": status["current"],
                "power": status["power"],
                "voltage_set": settings["voltage_set"],
                "current_set": settings["current_set"],
                "temp_internal": temps["internal"],
                "temp_external": temps["external"],
                "input_voltage": input_v,
                "ovp": protection["ovp"],
                "ocp": protection["ocp"],
                "protection_status": protection_status["status"],
                "ovp_triggered": protection_status["ovp_triggered"],
                "ocp_triggered": protection_status["ocp_triggered"],
                "amp_hours": energy["amp_hours"],
                "watt_hours": energy["watt_hours"],
                "backlight": backlight,
                "output_enabled": bool(output_state),
                "output_mode": output_mode,
                "buzzer": buzzer,
                "power_on_boot": power_on_boot,
                "take_out": take_out,
            }
            
            _LOGGER.debug("Successfully fetched data: %s", data)
            return data
            
        except Exception as err:
            self._consecutive_errors += 1
            _LOGGER.error(
                "Error communicating with device (attempt %d/%d): %s",
                self._consecutive_errors,
                self._max_consecutive_errors,
                err,
                exc_info=True,
            )
            self._connected = False
            
            # Only raise UpdateFailed after multiple consecutive failures
            # This prevents brief disconnections from making entities unavailable
            if self._consecutive_errors >= self._max_consecutive_errors:
                raise UpdateFailed(f"Failed to communicate after {self._consecutive_errors} attempts") from err
            
            # Return last known data to keep entities available
            return self.data if self.data else {}

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self._connected:
            try:
                await self.device.disconnect()
            except Exception:
                pass
            self._connected = False

    async def async_set_voltage(self, voltage: float) -> None:
        """Set output voltage."""
        await self.device.set_voltage(voltage)
        # Update the data directly without triggering unavailable state
        if self.data:
            self.data["voltage_set"] = voltage
            self.async_set_updated_data(self.data)

    async def async_set_current(self, current: float) -> None:
        """Set output current."""
        await self.device.set_current(current)
        # Update the data directly without triggering unavailable state
        if self.data:
            self.data["current_set"] = current
            self.async_set_updated_data(self.data)

    async def async_set_ovp(self, voltage: float) -> None:
        """Set over-voltage protection."""
        await self.device.set_ovp(voltage)
        # Update the data directly without triggering unavailable state
        if self.data:
            self.data["ovp"] = voltage
            self.async_set_updated_data(self.data)

    async def async_set_ocp(self, current: float) -> None:
        """Set over-current protection."""
        await self.device.set_ocp(current)
        # Update the data directly without triggering unavailable state
        if self.data:
            self.data["ocp"] = current
            self.async_set_updated_data(self.data)

    async def async_set_backlight(self, level: int) -> None:
        """Set backlight level."""
        await self.device.set_backlight(level)
        # Update the data directly without triggering unavailable state
        if self.data:
            self.data["backlight"] = level
            self.async_set_updated_data(self.data)

    async def async_set_output(self, state: bool) -> None:
        """Turn output on or off."""
        await self.device.set_output(state)
        # Update the data directly without triggering unavailable state
        if self.data:
            self.data["output_enabled"] = state
            self.async_set_updated_data(self.data)

    async def async_set_buzzer(self, state: bool) -> None:
        """Enable or disable buzzer."""
        await self.device.set_buzzer(state)
        # Update the data directly without triggering unavailable state
        if self.data:
            self.data["buzzer"] = state
            self.async_set_updated_data(self.data)

    async def async_set_power_on_boot(self, state: bool) -> None:
        """Enable or disable power on boot."""
        await self.device.set_power_on_boot(state)
        # Update the data directly without triggering unavailable state
        if self.data:
            self.data["power_on_boot"] = state
            self.async_set_updated_data(self.data)

    async def async_set_take_out(self, state: bool) -> None:
        """Enable or disable take out."""
        await self.device.set_take_out(state)
        # Update the data directly without triggering unavailable state
        if self.data:
            self.data["take_out"] = state
            self.async_set_updated_data(self.data)

    async def async_enable_connection(self) -> None:
        """Enable connection to device."""
        self._connection_enabled = True
        self._consecutive_errors = 0  # Reset error counter when re-enabling
        
        # Persist state to config entry
        new_data = dict(self.entry.data)
        new_data[CONF_CONNECTION_ENABLED] = True
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        
        await self.async_request_refresh()

    async def async_disable_connection(self) -> None:
        """Disable connection to device."""
        self._connection_enabled = False
        
        # Persist state to config entry
        new_data = dict(self.entry.data)
        new_data[CONF_CONNECTION_ENABLED] = False
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        
        if self._connected:
            try:
                await self.device.disconnect()
            except Exception:
                pass
            self._connected = False

    @property
    def connection_enabled(self) -> bool:
        """Return if connection is enabled."""
        return self._connection_enabled
