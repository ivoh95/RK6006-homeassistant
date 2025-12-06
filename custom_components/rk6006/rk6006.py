#!/usr/bin/env python3
"""
RK6006 Power Supply Bluetooth Control Demo

This script demonstrates basic control of the RK6006 programmable power supply
over Bluetooth using the Modbus RTU protocol.

Requirements:
    - bleak (for Bluetooth LE communication)
    - pymodbus (for Modbus protocol)

Install with: pip install bleak pymodbus
"""

import asyncio
import struct
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
from typing import Optional


class RK6006:
    """Controller for RK6006 Power Supply via Bluetooth"""
    
    # Device info
    REG_MODEL = 0x0000         # Model number (60066 = RK6006)
    REG_SERIAL_H = 0x0001      # Serial number high word
    REG_SERIAL_L = 0x0002      # Serial number low word
    REG_FIRMWARE = 0x0003      # Firmware version (div by 100)
    
    # Setpoint registers (read/write)
    REG_VOLTAGE_SET = 0x0008   # Voltage setting (0.01V)
    REG_CURRENT_SET = 0x0009   # Current setting (0.001A)
    
    # Output monitoring (actual values)
    REG_VOLTAGE_READ = 0x000A  # Actual output voltage (0.01V)
    REG_CURRENT_READ = 0x000B  # Actual output current (0.001A)
    REG_POWER_H = 0x000C       # Power reading high word (0.01W)
    REG_POWER_L = 0x000D       # Power reading low word (0.01W)
    
    # Input monitoring
    REG_INPUT_VOLTAGE = 0x000E # Input voltage (0.01V)
    
    # Control registers
    REG_OUTPUT_STATE = 0x0012  # Output on/off (1=on, 0=off)
    REG_OUTPUT_MODE = 0x0011   # Output mode (0=CV, 1=CC) [READ ONLY]
    REG_TAKE_OUT = 0x0043      # Take out (quick preset recall)
    REG_POWER_ON_BOOT = 0x0044 # Power on boot (auto-enable output)
    REG_BUZZER = 0x0045        # Buzzer on/off
    REG_BACKLIGHT = 0x0048     # Backlight brightness (0-5)
    
    # Temperature
    REG_TEMP_INT = 0x0005      # Internal temperature (1°C)
    REG_TEMP_EXT = 0x0004      # External temperature (1°C)
    
    # Protection setpoints (read/write)
    REG_OVP = 0x0052           # Over-voltage protection (0.01V)
    REG_OCP = 0x0053           # Over-current protection (0.001A)
    
    # Protection status (read-only)
    REG_PROTECTION = 0x0010    # Protection status (0=none, 1=OVP, 2=OCP)
    
    # Battery mode
    REG_BATTERY_MODE = 0x0032  # Battery mode (0=off, 1=on)
    REG_BATTERY_VOLTAGE = 0x0033  # Battery voltage (0.01V)
    
    # Energy counters (32-bit)
    REG_AH_H = 0x0026          # Amp-hours high word
    REG_AH_L = 0x0027          # Amp-hours low word
    REG_WH_H = 0x0028          # Watt-hours high word
    REG_WH_L = 0x0029          # Watt-hours low word
    
    # Memory slots (M0-M9, each uses 4 registers: V, I, OVP, OCP)
    REG_MEMORY_BASE = 0x0050   # Memory slot base (M0 at 0x50-0x53)
    
    # Bluetooth UUIDs (common for RK6006)
    UART_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
    UART_TX_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
    UART_RX_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
    
    def __init__(self, device_address: Optional[str] = None):
        """Initialize RK6006 controller
        
        Args:
            device_address: Bluetooth MAC address of the device (optional)
        """
        self.device_address = device_address
        self.ble_device: Optional[BLEDevice] = None
        self.client: Optional[BleakClient] = None
        self.response_data = bytearray()
        self.response_event = asyncio.Event()
        
    def _calculate_crc16(self, data: bytes) -> int:
        """Calculate Modbus CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    def _build_modbus_command(self, slave_id: int, function: int, 
                             register: int, value: int) -> bytes:
        """Build a Modbus RTU command"""
        data = struct.pack('>BBHH', slave_id, function, register, value)
        crc = self._calculate_crc16(data)
        return data + struct.pack('<H', crc)
    
    def _notification_handler(self, sender, data: bytearray):
        """Handle incoming Bluetooth notifications"""
        self.response_data.extend(data)
        # Check if we have a complete Modbus response
        # Read response: min 5 bytes [slave][func][len][data...][crc]
        # Write response: min 8 bytes [slave][func][addr_h][addr_l][val_h][val_l][crc_l][crc_h]
        if len(self.response_data) >= 5:
            func = self.response_data[1] if len(self.response_data) > 1 else 0
            if func == 0x03:  # Read response
                byte_count = self.response_data[2] if len(self.response_data) > 2 else 0
                expected_len = 5 + byte_count  # slave + func + len + data + 2-byte CRC
                if len(self.response_data) >= expected_len:
                    self.response_event.set()
            elif func == 0x06:  # Write response
                if len(self.response_data) >= 8:
                    self.response_event.set()
            else:
                # Unknown response, set event anyway
                self.response_event.set()
    
    async def scan_devices(self, timeout: float = 10.0):
        """Scan for RK6006 devices
        
        Args:
            timeout: Scan timeout in seconds
            
        Returns:
            List of discovered devices
        """
        print(f"Scanning for Bluetooth devices for {timeout} seconds...")
        devices = await BleakScanner.discover(timeout=timeout)
        
        rk_devices = []
        for device in devices:
            if device.name and "RK" in device.name.upper():
                rk_devices.append(device)
                print(f"Found: {device.name} ({device.address})")
        
        return rk_devices
    
    async def connect(self, timeout: float = 10.0):
        """Connect to the RK6006 device"""
        if not self.ble_device:
            # Need to scan for the device first
            print(f"Scanning for Bluetooth devices for {timeout} seconds...")
            devices = await BleakScanner.discover(timeout=timeout, return_adv=False)
            
            # Filter for RK6006 devices
            rk_devices = [
                d for d in devices 
                if d.name and d.name.startswith('RK6006')
            ]
            
            if not rk_devices:
                raise Exception("No RK6006 devices found")
            
            # Use the first device found or match by address
            if self.device_address:
                matching = [d for d in rk_devices if d.address == self.device_address]
                if matching:
                    self.ble_device = matching[0]
                else:
                    raise Exception(f"RK6006 device with address {self.device_address} not found")
            else:
                self.ble_device = rk_devices[0]
                self.device_address = self.ble_device.address
            
            print(f"Using device: {self.ble_device.name} ({self.device_address})")
        
        print(f"Connecting to {self.device_address}...")
        self.client = await establish_connection(
            BleakClient,
            self.ble_device,
            self.ble_device.name or self.device_address,
            disconnected_callback=lambda client: None,
        )
        
        # Start notifications
        await self.client.start_notify(
            self.UART_RX_CHAR_UUID, 
            self._notification_handler
        )
        print("Connected successfully!")
    
    async def disconnect(self):
        """Disconnect from the device"""
        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
                print("Disconnected")
            except Exception:
                # Ignore disconnect errors
                pass
    
    async def _send_command(self, command: bytes, timeout: float = 2.0) -> bytes:
        """Send a command and wait for response"""
        self.response_data.clear()
        self.response_event.clear()
        
        await self.client.write_gatt_char(self.UART_TX_CHAR_UUID, command)
        
        try:
            await asyncio.wait_for(self.response_event.wait(), timeout=timeout)
            response = bytes(self.response_data)
            # Small delay between commands to prevent issues
            await asyncio.sleep(0.05)
            return response
        except asyncio.TimeoutError:
            raise Exception("Command timeout - no response received")
    
    async def read_register(self, register: int, count: int = 1, slave_id: int = 1):
        """Read register value(s)
        
        Args:
            register: Register address
            count: Number of registers to read
            slave_id: Modbus slave ID (default: 1)
            
        Returns:
            Single value if count=1, list of values otherwise
        """
        command = self._build_modbus_command(slave_id, 0x03, register, count)
        response = await self._send_command(command)
        
        if len(response) >= 5:
            # Parse response: [slave_id][function][byte_count][data...][crc_low][crc_high]
            byte_count = response[2]
            expected_data = count * 2
            if byte_count == expected_data and len(response) >= 3 + byte_count + 2:
                values = []
                for i in range(count):
                    offset = 3 + (i * 2)
                    value = struct.unpack('>H', response[offset:offset+2])[0]
                    values.append(value)
                return values[0] if count == 1 else values
        raise Exception(f"Invalid response: {response.hex()}")
    
    async def write_register(self, register: int, value: int, slave_id: int = 1):
        """Write a register value
        
        Args:
            register: Register address
            value: Value to write
            slave_id: Modbus slave ID (default: 1)
        """
        command = self._build_modbus_command(slave_id, 0x06, register, value)
        response = await self._send_command(command)
        
        if len(response) < 8:
            raise Exception("Invalid response")
    
    async def set_voltage(self, voltage: float):
        """Set output voltage
        
        Args:
            voltage: Voltage in volts (e.g., 12.5)
        """
        value = int(voltage * 100)  # Convert to 0.01V units
        await self.write_register(self.REG_VOLTAGE_SET, value)
    
    async def set_current(self, current: float):
        """Set output current limit
        
        Args:
            current: Current in amperes (e.g., 2.5)
        """
        value = int(current * 1000)  # Convert to 0.001A units
        await self.write_register(self.REG_CURRENT_SET, value)
    
    async def get_voltage(self) -> float:
        """Read actual output voltage
        
        Returns:
            Voltage in volts
        """
        value = await self.read_register(self.REG_VOLTAGE_READ)
        return value / 100.0
    
    async def get_current(self) -> float:
        """Read actual output current
        
        Returns:
            Current in amperes
        """
        value = await self.read_register(self.REG_CURRENT_READ)
        return value / 1000.0
    
    async def get_power(self) -> float:
        """Read actual output power
        
        Returns:
            Power in watts
        """
        values = await self.read_register(self.REG_POWER_H, 2)
        power_raw = (values[0] << 16) | values[1]  # Combine 32-bit value
        return power_raw / 100.0
    
    async def set_output(self, state: bool):
        """Turn output on or off
        
        Args:
            state: True for ON, False for OFF
        """
        value = 1 if state else 0
        await self.write_register(self.REG_OUTPUT_STATE, value)
    
    async def get_output_mode(self) -> str:
        """Get current output mode (CV or CC)
        
        Returns:
            String: 'CV' for Constant Voltage, 'CC' for Constant Current
        """
        value = await self.read_register(self.REG_OUTPUT_MODE)
        return 'CC' if value == 1 else 'CV'
    
    async def get_status(self) -> dict:
        """Get current status of the power supply
        
        Returns:
            Dictionary with voltage, current, power readings
        """
        # Read output values in one batch (0x000A-0x000D = V, I, P_high, P_low)
        values = await self.read_register(self.REG_VOLTAGE_READ, 4)
        power_raw = (values[2] << 16) | values[3]  # Combine 32-bit power
        
        return {
            'voltage': values[0] / 100.0,
            'current': values[1] / 1000.0,
            'power': power_raw / 100.0
        }
    
    async def get_settings(self) -> dict:
        """Get current setpoint settings
        
        Returns:
            Dictionary with voltage and current setpoints
        """
        values = await self.read_register(self.REG_VOLTAGE_SET, 2)
        
        return {
            'voltage_set': values[0] / 100.0,
            'current_set': values[1] / 1000.0
        }
    
    # === Device Information Methods ===
    
    async def get_device_info(self) -> dict:
        """Get device information
        
        Returns:
            Dictionary with model, serial number, and firmware version
        """
        values = await self.read_register(self.REG_MODEL, 4)
        model = values[0]
        serial = (values[1] << 16) | values[2]
        firmware = values[3] / 100.0
        
        return {
            'model': model,
            'model_name': 'RK6006' if model == 60066 else f'Unknown ({model})',
            'serial': serial,
            'firmware': firmware
        }
    
    # === Temperature Methods ===
    
    async def get_temperature(self) -> dict:
        """Get temperature readings
        
        Returns:
            Dictionary with internal and external temperatures in °C
        """
        values = await self.read_register(self.REG_TEMP_INT, 2)
        
        # External temp shows 65535 if no probe connected
        ext_temp = float(values[1]) if values[1] < 65000 else None
        
        return {
            'internal': float(values[0]),
            'external': ext_temp
        }
    
    async def get_input_voltage(self) -> float:
        """Get input voltage
        
        Returns:
            Input voltage in volts
        """
        value = await self.read_register(self.REG_INPUT_VOLTAGE)
        return value / 100.0
    
    # === Protection Methods ===
    
    async def set_ovp(self, voltage: float):
        """Set over-voltage protection
        
        Args:
            voltage: OVP voltage in volts
        """
        value = int(voltage * 100)
        await self.write_register(self.REG_OVP, value)
    
    async def set_ocp(self, current: float):
        """Set over-current protection
        
        Args:
            current: OCP current in amperes
        """
        value = int(current * 1000)
        await self.write_register(self.REG_OCP, value)
    
    async def get_protection_settings(self) -> dict:
        """Get protection settings
        
        Returns:
            Dictionary with OVP and OCP values
        """
        values = await self.read_register(self.REG_OVP, 2)
        
        return {
            'ovp': values[0] / 100.0,
            'ocp': values[1] / 1000.0
        }
    
    async def get_protection_status(self) -> dict:
        """Get protection status
        
        Returns:
            Dictionary with protection status:
            - status: 'none', 'ovp', 'ocp', or 'unknown'
            - ovp_triggered: True if OVP is active
            - ocp_triggered: True if OCP is active
        """
        value = await self.read_register(self.REG_PROTECTION)
        
        if value == 0:
            status = 'none'
        elif value == 1:
            status = 'ovp'
        elif value == 2:
            status = 'ocp'
        else:
            status = 'unknown'
        
        return {
            'status': status,
            'ovp_triggered': value == 1,
            'ocp_triggered': value == 2,
        }
    
    # === Energy Counter Methods ===
    
    async def get_energy_counters(self) -> dict:
        """Get accumulated energy counters
        
        Returns:
            Dictionary with amp-hours and watt-hours
        """
        values = await self.read_register(self.REG_AH_H, 4)
        ah = ((values[0] << 16) | values[1]) / 1000.0
        wh = ((values[2] << 16) | values[3]) / 1000.0
        
        return {
            'amp_hours': ah,
            'watt_hours': wh
        }
    
    # === Memory Slot Methods ===
    
    async def save_memory(self, slot: int, voltage: float = None, 
                         current: float = None, ovp: float = None, 
                         ocp: float = None):
        """Save settings to a memory slot (M0-M9)
        
        Args:
            slot: Memory slot number (0-9)
            voltage: Voltage to save (if None, use current setting)
            current: Current to save (if None, use current setting)
            ovp: OVP to save (if None, use current setting)
            ocp: OCP to save (if None, use current setting)
        """
        if not 0 <= slot <= 9:
            raise ValueError("Memory slot must be 0-9")
        
        # Get current values if not specified
        if voltage is None or current is None:
            settings = await self.get_settings()
            voltage = voltage if voltage is not None else settings['voltage_set']
            current = current if current is not None else settings['current_set']
        
        if ovp is None or ocp is None:
            protection = await self.get_protection_settings()
            ovp = ovp if ovp is not None else protection['ovp']
            ocp = ocp if ocp is not None else protection['ocp']
        
        # Memory slots are at 0x50 + (slot * 4)
        base_addr = self.REG_MEMORY_BASE + (slot * 4)
        
        await self.write_register(base_addr, int(voltage * 100))
        await self.write_register(base_addr + 1, int(current * 1000))
        await self.write_register(base_addr + 2, int(ovp * 100))
        await self.write_register(base_addr + 3, int(ocp * 1000))
        
        print(f"Saved to memory M{slot}: {voltage:.2f}V, {current:.3f}A, "
              f"OVP={ovp:.2f}V, OCP={ocp:.3f}A")
    
    async def recall_memory(self, slot: int, apply: bool = True) -> dict:
        """Recall settings from a memory slot
        
        Args:
            slot: Memory slot number (0-9)
            apply: If True, apply the settings immediately
            
        Returns:
            Dictionary with the recalled settings
        """
        if not 0 <= slot <= 9:
            raise ValueError("Memory slot must be 0-9")
        
        base_addr = self.REG_MEMORY_BASE + (slot * 4)
        values = await self.read_register(base_addr, 4)
        
        settings = {
            'voltage': values[0] / 100.0,
            'current': values[1] / 1000.0,
            'ovp': values[2] / 100.0,
            'ocp': values[3] / 1000.0
        }
        
        if apply:
            await self.set_voltage(settings['voltage'])
            await self.set_current(settings['current'])
            await self.set_ovp(settings['ovp'])
            await self.set_ocp(settings['ocp'])
            print(f"Recalled and applied memory M{slot}")
        else:
            print(f"Recalled memory M{slot} (not applied)")
        
        return settings
    
    # === Battery Mode Methods ===
    
    async def set_battery_mode(self, enabled: bool, voltage: float = None):
        """Enable or disable battery charging mode
        
        Args:
            enabled: True to enable battery mode
            voltage: Battery voltage for charging (required if enabling)
        """
        if enabled and voltage is not None:
            await self.write_register(self.REG_BATTERY_VOLTAGE, int(voltage * 100))
        
        await self.write_register(self.REG_BATTERY_MODE, 1 if enabled else 0)
        print(f"Battery mode {'enabled' if enabled else 'disabled'}")
    
    async def get_battery_mode(self) -> dict:
        """Get battery mode status
        
        Returns:
            Dictionary with battery mode status and voltage
        """
        values = await self.read_register(self.REG_BATTERY_MODE, 2)
        
        return {
            'enabled': bool(values[0]),
            'voltage': values[1] / 100.0
        }
    
    # === Display Control Methods ===
    
    async def set_backlight(self, level: int):
        """Set display backlight brightness
        
        Args:
            level: Brightness level (0-5, where 0=off, 5=brightest)
        """
        if not 0 <= level <= 5:
            raise ValueError("Backlight level must be 0-5")
        
        await self.write_register(self.REG_BACKLIGHT, level)
        print(f"Backlight set to level {level}")
    
    async def get_backlight(self) -> int:
        """Get current backlight brightness level
        
        Returns:
            Brightness level (0-5)
        """
        return await self.read_register(self.REG_BACKLIGHT)
    
    # === Additional Settings Methods ===
    
    async def set_buzzer(self, enabled: bool):
        """Enable or disable buzzer
        
        Args:
            enabled: True to enable buzzer, False to disable
        """
        await self.write_register(self.REG_BUZZER, 1 if enabled else 0)
        print(f"Buzzer {'enabled' if enabled else 'disabled'}")
    
    async def get_buzzer(self) -> bool:
        """Get buzzer state
        
        Returns:
            True if buzzer is enabled, False otherwise
        """
        value = await self.read_register(self.REG_BUZZER)
        return bool(value)
    
    async def set_power_on_boot(self, enabled: bool):
        """Enable or disable power on boot (auto-enable output on power-up)
        
        Args:
            enabled: True to enable output on boot, False to disable
        """
        await self.write_register(self.REG_POWER_ON_BOOT, 1 if enabled else 0)
        print(f"Power on boot {'enabled' if enabled else 'disabled'}")
    
    async def get_power_on_boot(self) -> bool:
        """Get power on boot state
        
        Returns:
            True if power on boot is enabled, False otherwise
        """
        value = await self.read_register(self.REG_POWER_ON_BOOT)
        return bool(value)
    
    async def set_take_out(self, enabled: bool):
        """Enable or disable take out (quick preset recall)
        
        Args:
            enabled: True to enable take out, False to disable
        """
        await self.write_register(self.REG_TAKE_OUT, 1 if enabled else 0)
        print(f"Take out {'enabled' if enabled else 'disabled'}")
    
    async def get_take_out(self) -> bool:
        """Get take out state
        
        Returns:
            True if take out is enabled, False otherwise
        """
        value = await self.read_register(self.REG_TAKE_OUT)
        return bool(value)

