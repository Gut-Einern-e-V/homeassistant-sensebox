"""Binary sensor platform for openSenseMap Sensors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, INACTIVITY_THRESHOLD
from .coordinator import OpenSenseMapCoordinator
from .utils import parse_timestamp


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up openSenseMap binary sensors from a config entry."""
    coordinator: OpenSenseMapCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OpenSenseMapInactivityBinarySensor(coordinator, entry)])


class OpenSenseMapInactivityBinarySensor(
    CoordinatorEntity[OpenSenseMapCoordinator], BinarySensorEntity
):
    """Reports whether the senseBox appears inactive."""

    _attr_has_entity_name = True
    _attr_name = "Inactivity alarm"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(
        self, coordinator: OpenSenseMapCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the status entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_inactivity_alarm"

    @property
    def is_on(self) -> bool:
        """Return True when no sensor has recent data."""
        if self.coordinator.data is None:
            return True

        newest_measurement = self._newest_measurement_at()
        if newest_measurement is None:
            return True

        age = datetime.now(timezone.utc) - newest_measurement
        return age > INACTIVITY_THRESHOLD

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose diagnostic status data for automations and troubleshooting."""
        newest_measurement = self._newest_measurement_at()
        return {
            "inactivity_threshold_seconds": int(INACTIVITY_THRESHOLD.total_seconds()),
            "latest_measurement_at": (
                newest_measurement.isoformat() if newest_measurement else None
            ),
            "active_sensor_count": self._active_sensor_count(),
            "total_sensor_count": (
                len(self.coordinator.data.sensors) if self.coordinator.data else 0
            ),
        }

    def _newest_measurement_at(self) -> datetime | None:
        """Return the newest valid measurement timestamp among all sensors."""
        if self.coordinator.data is None:
            return None
        timestamps = [
            parsed
            for sensor in self.coordinator.data.sensors.values()
            if (parsed := parse_timestamp(sensor.get("last_measurement_at"))) is not None
        ]
        return max(timestamps) if timestamps else None

    def _active_sensor_count(self) -> int:
        """Return number of sensors with fresh measurements."""
        if self.coordinator.data is None:
            return 0
        now = datetime.now(timezone.utc)
        return sum(
            1
            for sensor in self.coordinator.data.sensors.values()
            if (
                measured_at := parse_timestamp(sensor.get("last_measurement_at"))
            )
            is not None
            and (now - measured_at) <= INACTIVITY_THRESHOLD
        )
