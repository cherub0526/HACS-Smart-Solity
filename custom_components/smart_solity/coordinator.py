"""Data update coordinator for Smart Solity."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SmartSolityApi, SmartSolityAuthError, SmartSolityError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SmartSolityCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Polls /api_v2/myDevice and exposes devices keyed by myDeviceId."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: SmartSolityApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            config_entry=entry,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.api.get_devices()
        except SmartSolityAuthError as err:
            # Let HA trigger reauth.
            from homeassistant.exceptions import ConfigEntryAuthFailed

            raise ConfigEntryAuthFailed(str(err)) from err
        except SmartSolityError as err:
            raise UpdateFailed(str(err)) from err

        result: dict[str, dict[str, Any]] = {}
        for dev in devices:
            device_id = dev.get("myDeviceId")
            if device_id:
                result[str(device_id)] = dev
        return result
