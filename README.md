# openSenseMap Sensors for Home Assistant

[![Add to Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Gut-Einern-e-V&repository=homeassistant-sensebox&category=integration)

[![HACS](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/Gut-Einern-e-V/homeassistant-sensebox?style=for-the-badge)](https://github.com/Gut-Einern-e-V/homeassistant-sensebox/releases)
[![Validate](https://img.shields.io/github/actions/workflow/status/Gut-Einern-e-V/homeassistant-sensebox/validate.yml?label=Validate&style=for-the-badge)](https://github.com/Gut-Einern-e-V/homeassistant-sensebox/actions/workflows/validate.yml)

A Home Assistant custom integration that fetches sensor data from [openSenseMap](https://opensensemap.org) senseBox stations via their public API.

## Features

- **Config Flow** – set up via the UI (Settings → Integrations → Add → "openSenseMap Sensors")
- **Automatic sensor discovery** – creates one entity per active sensor on your senseBox
- **Inactivity alarm binary sensor** – reports a problem when no sensor has sent new data for 10 minutes
- **Supports all common senseBox sensors**: PM2.5, PM10, Temperature, Humidity, Pressure, UV, Illuminance, Sound Level, Soil Moisture, Wind Speed, CO₂, VOC, and more
- **Proper HA device classes** – enables long-term statistics, energy dashboard compatibility, etc.
- **Cloud polling** via `DataUpdateCoordinator` (default: every 5 minutes)
- **No external dependencies** – uses HA's built-in `aiohttp` session
- **Tested with Home Assistant 2026.3**

## Installation

### HACS (recommended)

Click the button below to add this integration via HACS:

[![Add to Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Gut-Einern-e-V&repository=homeassistant-sensebox&category=integration)

Or install manually via HACS:

1. Open HACS in your Home Assistant instance.
2. Click the **⋮** menu → **Custom repositories**.
3. Add `https://github.com/Gut-Einern-e-V/homeassistant-sensebox` as an **Integration**.
4. Search for **openSenseMap Sensors** and install it.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/opensensemap_sensors` folder into your HA `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **openSenseMap Sensors**.
3. Enter your senseBox **Station ID** (the 24-character hex ID from opensensemap.org).
4. Optionally adjust the polling interval (default: 300 seconds).

## Finding your Station ID

1. Go to [opensensemap.org](https://opensensemap.org).
2. Click on your senseBox on the map.
3. The URL will look like `https://opensensemap.org/explore/63b2ab763ee774001b3585b1` – the last part is your Station ID.

## License

MIT
