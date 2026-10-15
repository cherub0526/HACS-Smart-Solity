"""DataUpdateCoordinator for the 3elock integration."""

from __future__ import annotations

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
    SmartSolityStatus,
)
from .const import DOMAIN, LOGGER, UPDATE_INTERVAL

type SmartSolityConfigEntry = ConfigEntry[SmartSolityDataUpdateCoordinator]


class SmartSolityDataUpdateCoordinator(DataUpdateCoordinator[SmartSolityStatus]):
    """Coordinator that polls the lock status."""

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
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.device = device

    async def _async_update_data(self) -> SmartSolityStatus:
        """Poll for a lock status change.

        The API responds with HTTP 304 when nothing has changed since the
        last poll, in which case the previous status is kept as-is.
        """
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
