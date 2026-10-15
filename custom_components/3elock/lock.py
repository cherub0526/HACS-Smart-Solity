"""Lock platform for Smart Solity."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartSolityConfigEntry
from .api import SmartSolityError
from .const import (
    CONTROL_CLOSE,
    CONTROL_OPEN,
    LOCKED_TOKENS,
    OPTION_DEFAULT,
    UNLOCKED_TOKENS,
)
from .entity import SmartSolityEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartSolityConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        SmartSolityLock(coordinator, device_id) for device_id in coordinator.data
    )


class SmartSolityLock(SmartSolityEntity, LockEntity):
    """A Smart Solity door lock, controlled via the cloud API."""

    _attr_name = None  # use the device name
    # Remote unlock ("open") exists in the API but may be gated by the
    # lock's firmware / dual-auth settings. Advertise OPEN; the server
    # decides whether it is honored.
    _attr_supported_features = LockEntityFeature.OPEN

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_lock"

    @property
    def is_locked(self) -> bool | None:
        status = str(self.device.get("lockerStatus", "")).strip().lower()
        if status in {t.lower() for t in LOCKED_TOKENS}:
            return True
        if status in {t.lower() for t in UNLOCKED_TOKENS}:
            return False
        return None

    async def async_lock(self, **kwargs: Any) -> None:
        await self._control(CONTROL_CLOSE, OPTION_DEFAULT)

    async def async_unlock(self, **kwargs: Any) -> None:
        await self._control(CONTROL_OPEN, OPTION_DEFAULT)

    async def async_open(self, **kwargs: Any) -> None:
        await self._control(CONTROL_OPEN, OPTION_DEFAULT)

    async def _control(self, control_type: str, option: str) -> None:
        try:
            await self.coordinator.api.control(self._device_id, control_type, option)
        except SmartSolityError as err:
            raise HomeAssistantError(f"Smart Solity control failed: {err}") from err
        # State is confirmed by the next poll; refresh promptly.
        await self.coordinator.async_request_refresh()
