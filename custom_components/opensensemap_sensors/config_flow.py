"""Config flow for openSenseMap Sensors."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_URL,
    CONF_SCAN_INTERVAL,
    CONF_STATION_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
ACTIVE_LOOKBACK_DAYS = 10
BOXES_API_URL = "https://api.opensensemap.org/boxes"
CONF_NEARBY_RADIUS_KM = "nearby_radius_km"
DEFAULT_NEARBY_RADIUS_KM = 20

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_STATION_ID, default=""): str,
        vol.Optional(CONF_NEARBY_RADIUS_KM, default=DEFAULT_NEARBY_RADIUS_KM): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=200)
        ),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=60, max=3600)
        ),
    }
)


class OpenSenseMapConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for openSenseMap Sensors."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._scan_interval = DEFAULT_SCAN_INTERVAL
        self._nearby_stations: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step – user enters the station ID."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input.get(CONF_STATION_ID, "").strip()
            self._scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            if not station_id:
                stations, error = await self._get_nearby_active_stations(
                    radius_km=user_input.get(CONF_NEARBY_RADIUS_KM, DEFAULT_NEARBY_RADIUS_KM)
                )
                if error:
                    errors["base"] = error
                elif not stations:
                    errors["base"] = "no_active_nearby"
                else:
                    self._nearby_stations = stations
                    return await self.async_step_nearby()
            else:
                # Prevent duplicate entries for the same station.
                await self.async_set_unique_id(station_id)
                self._abort_if_unique_id_configured()

                # Validate that the API responds with valid data.
                box_name, error = await self._test_station(station_id)
                if error:
                    errors["base"] = error
                else:
                    return self.async_create_entry(
                        title=box_name or station_id,
                        data={
                            CONF_STATION_ID: station_id,
                            CONF_SCAN_INTERVAL: self._scan_interval,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_nearby(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user select an active nearby station from a dropdown."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]

            await self.async_set_unique_id(station_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self._nearby_stations.get(station_id, station_id),
                data={
                    CONF_STATION_ID: station_id,
                    CONF_SCAN_INTERVAL: self._scan_interval,
                },
            )

        if not self._nearby_stations:
            errors["base"] = "no_active_nearby"
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )

        return self.async_show_form(
            step_id="nearby",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATION_ID): vol.In(self._nearby_stations),
                }
            ),
            errors=errors,
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    async def _test_station(self, station_id: str) -> tuple[str | None, str | None]:
        """Test whether the station exists and return (box_name, error_key)."""
        url = API_URL.format(station_id=station_id)
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 404:
                    return None, "station_not_found"
                resp.raise_for_status()
                data = await resp.json()
                return data.get("name", station_id), None
        except (aiohttp.ClientError, TimeoutError):
            _LOGGER.exception("Error connecting to openSenseMap API")
            return None, "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during station validation")
            return None, "unknown"

    async def _get_nearby_active_stations(
        self, radius_km: int
    ) -> tuple[dict[str, str], str | None]:
        """Fetch nearby stations and keep only active senseBoxes."""
        latitude = self.hass.config.latitude
        longitude = self.hass.config.longitude
        if latitude is None or longitude is None:
            return {}, "location_not_set"

        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=ACTIVE_LOOKBACK_DAYS)
        max_distance = str(radius_km * 1000)

        try:
            boxes = await self._fetch_nearby_boxes(f"{latitude},{longitude}", max_distance)
            if not any(self._is_active_box(box, cutoff) for box in boxes):
                boxes = await self._fetch_nearby_boxes(f"{longitude},{latitude}", max_distance)
        except (aiohttp.ClientError, TimeoutError):
            _LOGGER.exception("Error loading nearby senseBoxes from openSenseMap API")
            return {}, "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during nearby senseBox lookup")
            return {}, "unknown"

        stations: dict[str, str] = {}
        for box in boxes if isinstance(boxes, list) else []:
            station_id = box.get("_id")
            if not station_id or not self._is_active_box(box, cutoff):
                continue
            name = box.get("name", station_id)
            stations[station_id] = f"{name} ({station_id})"

        return dict(sorted(stations.items(), key=lambda item: item[1].lower())), None

    async def _fetch_nearby_boxes(self, near: str, max_distance: str) -> list[dict[str, Any]]:
        """Fetch nearby boxes from the openSenseMap API."""
        session = async_get_clientsession(self.hass)
        params = {"near": near, "maxDistance": max_distance}
        async with session.get(
            BOXES_API_URL,
            params=params,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json()

        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    @staticmethod
    def _is_active_box(box: dict[str, Any], cutoff: datetime) -> bool:
        """Return True if the senseBox has measurements newer than cutoff."""
        updated_at = OpenSenseMapConfigFlow._parse_timestamp(box.get("updatedAt"))
        if updated_at and updated_at >= cutoff:
            return True

        for sensor in box.get("sensors", []):
            last_measurement = sensor.get("lastMeasurement", {})
            measured_at = OpenSenseMapConfigFlow._parse_timestamp(last_measurement.get("createdAt"))
            if measured_at and measured_at >= cutoff:
                return True

        return False

    @staticmethod
    def _parse_timestamp(raw_timestamp: Any) -> datetime | None:
        """Parse ISO timestamps from API responses to timezone-aware datetimes."""
        if not isinstance(raw_timestamp, str):
            return None

        normalized = raw_timestamp.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
