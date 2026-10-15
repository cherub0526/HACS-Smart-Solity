"""Lock platform for the 3elock integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import voluptuous as vol

from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SmartSolityApiError, SmartSolityConnectionError
from .coordinator import SmartSolityConfigEntry, SmartSolityDataUpdateCoordinator
from .entity import SmartSolityEntity

SERVICE_CREATE_OTP = "create_one_time_password"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SmartSolityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the lock entity and its services."""
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_CREATE_OTP,
        {
            vol.Required("code"): cv.string,
            vol.Required("start"): cv.datetime,
            vol.Required("end"): cv.datetime,
        },
        "async_create_one_time_password",
    )
    async_add_entities([SmartSolityLock(config_entry.runtime_data.status)])


class SmartSolityLock(SmartSolityEntity, LockEntity):
    """Representation of a Solity lock."""

    _attr_name = None

    def __init__(self, coordinator: SmartSolityDataUpdateCoordinator) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.device.device_id
        # Optimistic state set right after a lock/unlock action; held until the
        # polled device state catches up (confirms it), so the UI reacts instantly.
        self._optimistic_locked: bool | None = None

    @property
    def is_locked(self) -> bool:
        """Return true if the lock is locked (lockerStatus == '0')."""
        if self._optimistic_locked is not None:
            return self._optimistic_locked
        return self.coordinator.data.get("lockerStatus") == "0"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Clear the optimistic state once the server confirms the new value."""
        if self._optimistic_locked is not None:
            real_locked = self.coordinator.data.get("lockerStatus") == "0"
            if real_locked == self._optimistic_locked:
                self._optimistic_locked = None
        super()._handle_coordinator_update()

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device (optimistic: show locked immediately)."""
        try:
            await self.coordinator.api.lock(self.coordinator.device.device_id)
        except (SmartSolityApiError, SmartSolityConnectionError) as err:
            raise HomeAssistantError(str(err)) from err
        self._optimistic_locked = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device (optimistic: show unlocked immediately)."""
        try:
            await self.coordinator.api.unlock(self.coordinator.device.device_id)
        except (SmartSolityApiError, SmartSolityConnectionError) as err:
            raise HomeAssistantError(str(err)) from err
        self._optimistic_locked = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_create_one_time_password(
        self, code: str, start: datetime, end: datetime
    ) -> None:
        """Create a one-time password on the lock, valid in the given window."""
        if end <= start:
            raise HomeAssistantError("`end` must be after `start`")
        try:
            await self.coordinator.api.create_one_time_password(
                self.coordinator.device.device_id, code, start, end
            )
        except (SmartSolityApiError, SmartSolityConnectionError) as err:
            raise HomeAssistantError(str(err)) from err
