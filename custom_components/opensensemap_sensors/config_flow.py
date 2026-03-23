"""Config flow for openSenseMap Sensors."""

from __future__ import annotations

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

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STATION_ID): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=60, max=3600)
        ),
    }
)


class OpenSenseMapConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for openSenseMap Sensors."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step – user enters the station ID."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID].strip()

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
                        CONF_SCAN_INTERVAL: user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
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
