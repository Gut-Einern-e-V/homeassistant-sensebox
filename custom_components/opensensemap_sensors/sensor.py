"""Sensor platform for openSenseMap Sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_STATION_ID,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    SENSOR_DEVICE_CLASS_MAP,
    SENSOR_ICON_MAP,
)
from .coordinator import OpenSenseMapCoordinator, OpenSenseMapData

_LOGGER = logging.getLogger(__name__)

# ── Unit → HA unit normalisation ─────────────────────────────────────────────
# The API sometimes uses non‑standard symbols. We normalise them so that HA
# records statistics correctly.
UNIT_MAP: dict[str, str] = {
    "°c": "°C",
    "°f": "°F",
    "%": "%",
    "hpa": "hPa",
    "pa": "Pa",
    "lux": "lx",
    "µg/m³": "µg/m³",
    "µw/cm²": "µW/cm²",
    "db": "dB",
    "db(a)": "dB(A)",
    "mm": "mm",
    "m/s": "m/s",
    "km/h": "km/h",
    "v": "V",
    "ppm": "ppm",
    "ppb": "ppb",
}


def _normalise_unit(raw_unit: str) -> str:
    """Return a normalised version of the unit string."""
    return UNIT_MAP.get(raw_unit.lower().strip(), raw_unit)


def _resolve_device_class(title: str) -> SensorDeviceClass | None:
    """Look up the HA device class for a given sensor title."""
    return SENSOR_DEVICE_CLASS_MAP.get(title.lower().strip())


def _resolve_icon(title: str) -> str | None:
    """Look up a fallback MDI icon for a given sensor title."""
    return SENSOR_ICON_MAP.get(title.lower().strip())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up openSenseMap sensor entities from a config entry."""
    coordinator: OpenSenseMapCoordinator = hass.data[DOMAIN][entry.entry_id]

    station_id: str = entry.data[CONF_STATION_ID]

    entities: list[OpenSenseMapSensor] = [
        OpenSenseMapSensor(
            coordinator=coordinator,
            entry=entry,
            station_id=station_id,
            sensor_id=sensor_id,
            sensor_info=sensor_info,
        )
        for sensor_id, sensor_info in coordinator.data.sensors.items()
    ]

    async_add_entities(entities)


class OpenSenseMapSensor(CoordinatorEntity[OpenSenseMapCoordinator], SensorEntity):
    """Representation of a single senseBox sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: OpenSenseMapCoordinator,
        entry: ConfigEntry,
        station_id: str,
        sensor_id: str,
        sensor_info: dict[str, Any],
    ) -> None:
        """Initialise the sensor entity."""
        super().__init__(coordinator)

        self._sensor_id = sensor_id
        title: str = sensor_info["title"]

        # ── Unique ID ────────────────────────────────────────────────────
        self._attr_unique_id = f"{entry.entry_id}_{sensor_id}"

        # ── Display name (entity name shown beneath the device) ──────────
        self._attr_name = title

        # ── Device class & icon ──────────────────────────────────────────
        device_class = _resolve_device_class(title)
        if device_class is not None:
            self._attr_device_class = device_class
        icon = _resolve_icon(title)
        if icon is not None:
            self._attr_icon = icon

        # ── Unit ─────────────────────────────────────────────────────────
        raw_unit = sensor_info.get("unit", "")
        self._attr_native_unit_of_measurement = _normalise_unit(raw_unit) if raw_unit else None

        # ── Device info (all sensors belong to the same Box device) ──────
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=coordinator.data.box_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=f"https://opensensemap.org/explore/{station_id}",
        )

    # ── State ────────────────────────────────────────────────────────────────

    @property
    def native_value(self) -> float | str | None:
        """Return the current sensor value."""
        sensor_data = self._get_sensor_data()
        if sensor_data is None:
            return None
        raw = sensor_data.get("value")
        if raw is None:
            return None
        # Try to convert to float for numeric sensors; fall back to string.
        try:
            return float(raw)
        except (ValueError, TypeError):
            return raw

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose additional context as state attributes."""
        sensor_data = self._get_sensor_data()
        if sensor_data is None:
            return None
        attrs: dict[str, Any] = {}
        if sensor_data.get("sensor_type"):
            attrs["sensor_type"] = sensor_data["sensor_type"]
        if sensor_data.get("last_measurement_at"):
            attrs["last_measurement_at"] = sensor_data["last_measurement_at"]
        return attrs if attrs else None

    # ── Availability ─────────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        """Return True if coordinator data contains our sensor."""
        return super().available and self._get_sensor_data() is not None

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_sensor_data(self) -> dict[str, Any] | None:
        """Safely retrieve this sensor's data dict from the coordinator."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.sensors.get(self._sensor_id)
