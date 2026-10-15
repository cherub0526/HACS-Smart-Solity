"""Lock platform for the 3elock integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SmartSolityApiError, SmartSolityConnectionError
from .coordinator import SmartSolityConfigEntry, SmartSolityDataUpdateCoordinator
from .entity import SmartSolityEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SmartSolityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the lock entity."""
    async_add_entities([SmartSolityLock(config_entry.runtime_data)])


class SmartSolityLock(SmartSolityEntity, LockEntity):
    """Representation of a Solity lock."""

    _attr_name = None

    def __init__(self, coordinator: SmartSolityDataUpdateCoordinator) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.device.device_id

    @property
    def is_locked(self) -> bool:
        """Return true if the lock is locked (lockerStatus == '0')."""
        return self.coordinator.data.get("lockerStatus") == "0"

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        try:
            await self.coordinator.api.lock(self.coordinator.device.device_id)
        except (SmartSolityApiError, SmartSolityConnectionError) as err:
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        try:
            await self.coordinator.api.unlock(self.coordinator.device.device_id)
        except (SmartSolityApiError, SmartSolityConnectionError) as err:
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()
