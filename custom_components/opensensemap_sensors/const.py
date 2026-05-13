"""Constants for the openSenseMap Sensors integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "opensensemap_sensors"

# ── Config keys ──────────────────────────────────────────────────────────────
CONF_STATION_ID: Final = "station_id"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_SCAN_INTERVAL: Final = 300  # seconds (5 minutes)
INACTIVITY_THRESHOLD: Final = timedelta(minutes=10)

# ── API ──────────────────────────────────────────────────────────────────────
API_URL: Final = "https://api.opensensemap.org/boxes/{station_id}"

# ── Device info ──────────────────────────────────────────────────────────────
MANUFACTURER: Final = "openSenseMap"
MODEL: Final = "senseBox"

# ── Sensor‑title → HA device_class mapping ───────────────────────────────────
# Keys are **lowercased** sensor titles coming from the API.
# Values are (device_class | None, icon | None) tuples.
# device_class=None means HA will use the icon instead.
from homeassistant.components.sensor import SensorDeviceClass  # noqa: E402

SENSOR_DEVICE_CLASS_MAP: dict[str, SensorDeviceClass | None] = {
    "pm2.5": SensorDeviceClass.PM25,
    "pm10": SensorDeviceClass.PM10,
    "temperatur": SensorDeviceClass.TEMPERATURE,
    "temperature": SensorDeviceClass.TEMPERATURE,
    "rel. luftfeuchte": SensorDeviceClass.HUMIDITY,
    "luftfeuchte": SensorDeviceClass.HUMIDITY,
    "humidity": SensorDeviceClass.HUMIDITY,
    "relative humidity": SensorDeviceClass.HUMIDITY,
    "luftdruck": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
    "atm. luftdruck": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
    "atmospheric pressure": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
    "pressure": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
    "beleuchtungsstärke": SensorDeviceClass.ILLUMINANCE,
    "illuminance": SensorDeviceClass.ILLUMINANCE,
    "uv-intensität": SensorDeviceClass.IRRADIANCE,
    "uv-intensity": SensorDeviceClass.IRRADIANCE,
    "uv intensity": SensorDeviceClass.IRRADIANCE,
    "lautstärke": SensorDeviceClass.SOUND_PRESSURE,
    "sound level": SensorDeviceClass.SOUND_PRESSURE,
    "bodenfeuchte": SensorDeviceClass.MOISTURE,
    "soil moisture": SensorDeviceClass.MOISTURE,
    "niederschlag": SensorDeviceClass.PRECIPITATION,
    "precipitation": SensorDeviceClass.PRECIPITATION,
    "windgeschwindigkeit": SensorDeviceClass.WIND_SPEED,
    "wind speed": SensorDeviceClass.WIND_SPEED,
    "spannung": SensorDeviceClass.VOLTAGE,
    "voltage": SensorDeviceClass.VOLTAGE,
    "batterie": SensorDeviceClass.BATTERY,
    "battery": SensorDeviceClass.BATTERY,
    "co2": SensorDeviceClass.CO2,
    "voc": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
}

# Fallback icons when no device_class matches.
SENSOR_ICON_MAP: dict[str, str] = {
    "pm2.5": "mdi:molecule",
    "pm10": "mdi:molecule",
    "temperatur": "mdi:thermometer",
    "temperature": "mdi:thermometer",
    "rel. luftfeuchte": "mdi:water-percent",
    "luftfeuchte": "mdi:water-percent",
    "humidity": "mdi:water-percent",
    "luftdruck": "mdi:gauge",
    "pressure": "mdi:gauge",
    "beleuchtungsstärke": "mdi:brightness-5",
    "illuminance": "mdi:brightness-5",
    "uv-intensität": "mdi:sun-wireless",
    "uv-intensity": "mdi:sun-wireless",
    "lautstärke": "mdi:volume-high",
    "sound level": "mdi:volume-high",
    "bodenfeuchte": "mdi:water",
    "soil moisture": "mdi:water",
    "niederschlag": "mdi:weather-pouring",
    "precipitation": "mdi:weather-pouring",
    "windgeschwindigkeit": "mdi:weather-windy",
    "wind speed": "mdi:weather-windy",
    "co2": "mdi:molecule-co2",
    "voc": "mdi:air-filter",
}
