# RK6006 Power Supply for Home Assistant

Home Assistant integration for the Ruideng RK6006 Bluetooth-enabled power supply.

## Features

- **Real-time monitoring**: Voltage, current, power, temperature, input voltage
- **Output control**: Turn output on/off via switch
- **Protection monitoring**: Over-voltage (OVP) and over-current (OCP) status with binary sensors
- **Mode detection**: CV (Constant Voltage) and CC (Constant Current) mode indicators
- **Configuration**: Set voltage, current, OVP, OCP levels via number entities
- **Display settings**: Adjust backlight brightness
- **System settings**: Configure buzzer, power-on boot behavior, and take-out feature
- **Connection management**: Enable/disable Bluetooth connection with persistent state

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/ivoh95/RK6006-homeassistant`
6. Select category "Integration"
7. Click "Add"
8. Search for "RK6006" and install

### Manual Installation

1. Copy the `custom_components/rk6006` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "RK6006"
4. Select your RK6006 device from the discovered Bluetooth devices
5. The integration will be added automatically

## Entities

The integration creates the following entities:

**Sensors:**
- Voltage (V)
- Current (A)
- Power (W)
- Temperature (°C)
- Input Voltage (V)
- Protection Status (text: NONE/OVP/OCP)

**Binary Sensors:**
- CV Mode (on when in Constant Voltage mode)
- CC Mode (on when in Constant Current mode)
- OVP Triggered (on when over-voltage protection activated)
- OCP Triggered (on when over-current protection activated)

**Switches:**
- Output Enable/Disable
- Connection Enable/Disable
- Buzzer Enable/Disable
- Power On Boot
- Take Out

**Numbers:**
- Set Voltage (V)
- Set Current (A)
- OVP Threshold (V)
- OCP Threshold (A)
- Backlight Level (0-5)

## Requirements

- Home Assistant with Bluetooth support
- RK6006 power supply with Bluetooth enabled

## License

MIT License
