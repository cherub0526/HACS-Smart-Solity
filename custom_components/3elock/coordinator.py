"""DataUpdateCoordinators for the 3elock integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SmartSolityApiClient,
    SmartSolityApiError,
    SmartSolityAuthError,
    SmartSolityConnectionError,
    SmartSolityDevice,
)
from .const import DOMAIN, LOG_UPDATE_INTERVAL, LOGGER, UPDATE_INTERVAL


class SmartSolityDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the lock status (fast, 304-aware)."""

    config_entry: SmartSolityConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SmartSolityConfigEntry,
        api: SmartSolityApiClient,
        device: SmartSolityDevice,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_status",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.device = device

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll for a lock status change (keeps previous data on HTTP 304)."""
        try:
            status = await self.api.get_device_status()
        except SmartSolityAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (SmartSolityApiError, SmartSolityConnectionError) as err:
            raise UpdateFailed(str(err)) from err
        if status is None:
            if self.data is None:
                raise UpdateFailed("myDevice reported no change on the initial poll")
            return self.data
        return status


class SmartSolityLogCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator that polls the access log (slow)."""

    config_entry: SmartSolityConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: SmartSolityConfigEntry,
        api: SmartSolityApiClient,
        device: SmartSolityDevice,
        timezone: str,
    ) -> None:
        """Initialize the log coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_log",
            update_interval=LOG_UPDATE_INTERVAL,
        )
        self.api = api
        self.device = device
        self._timezone = timezone

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch the most recent access-log entries."""
        try:
            return await self.api.get_logs(
                self.device.device_id, length=20, timezone=self._timezone
            )
        except SmartSolityAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (SmartSolityApiError, SmartSolityConnectionError) as err:
            raise UpdateFailed(str(err)) from err


@dataclass
class SmartSolityRuntimeData:
    """Everything the platforms need, stored on the config entry."""

    device: SmartSolityDevice
    status: SmartSolityDataUpdateCoordinator
    logs: SmartSolityLogCoordinator


type SmartSolityConfigEntry = ConfigEntry[SmartSolityRuntimeData]
