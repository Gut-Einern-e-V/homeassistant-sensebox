"""DataUpdateCoordinator for openSenseMap Sensors."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, CONF_SCAN_INTERVAL, CONF_STATION_ID, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class OpenSenseMapData:
    """Typed wrapper around the parsed API response."""

    def __init__(
        self,
        box_name: str,
        sensors: dict[str, dict[str, Any]],
    ) -> None:
        self.box_name = box_name
        self.sensors = sensors


class OpenSenseMapCoordinator(DataUpdateCoordinator[OpenSenseMapData]):
    """Fetch data from the openSenseMap API and provide it to entities."""

    def __init__(self, hass: HomeAssistant, entry_data: dict[str, Any]) -> None:
        """Initialise the coordinator."""
        self._station_id: str = entry_data[CONF_STATION_ID]
        self._scan_interval: int = entry_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self._api_url: str = API_URL.format(station_id=self._station_id)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self._scan_interval),
        )

    # ── Core fetch & parse ──────────────────────────────────────────────────

    async def _async_update_data(self) -> OpenSenseMapData:
        """Fetch the latest data from the openSenseMap API."""
        try:
            raw = await self._fetch_api()
            return self._parse(raw)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Connection error while fetching data: {err}") from err
        except (KeyError, ValueError) as err:
            raise UpdateFailed(f"Unexpected API response: {err}") from err

    async def _fetch_api(self) -> dict[str, Any]:
        """Perform the actual HTTP GET request."""
        session = async_get_clientsession(self.hass)
        async with session.get(self._api_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            resp.raise_for_status()
            return await resp.json()  # type: ignore[return-value]

    @staticmethod
    def _parse(data: dict[str, Any]) -> OpenSenseMapData:
        """Parse the raw API JSON into a structured format.

        Only sensors that have a ``lastMeasurement`` with a ``value`` field are
        included – sensors that have never reported are silently skipped.
        """
        box_name: str = data.get("name", "senseBox")
        sensors: dict[str, dict[str, Any]] = {}

        for sensor in data.get("sensors", []):
            title: str | None = sensor.get("title")
            last: dict[str, Any] | None = sensor.get("lastMeasurement")
            if not title or not last or "value" not in last:
                continue

            # Build a clean key from the sensor's unique _id to avoid title
            # collisions on boxes that expose multiple sensors with the same
            # human‑readable name.
            sensor_id: str = sensor["_id"]

            sensors[sensor_id] = {
                "title": title,
                "value": last["value"],
                "unit": sensor.get("unit", ""),
                "sensor_type": sensor.get("sensorType", ""),
                "icon": sensor.get("icon", ""),
                "last_measurement_at": last.get("createdAt"),
            }

        return OpenSenseMapData(box_name=box_name, sensors=sensors)
