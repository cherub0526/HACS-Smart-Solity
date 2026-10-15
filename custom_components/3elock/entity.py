"""Base entity for the 3elock integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .api import SmartSolityDevice
from .const import DOMAIN, MANUFACTURER


class SmartSolityEntity(CoordinatorEntity[DataUpdateCoordinator]):
    """Base entity for a lock device.

    Works with any coordinator that exposes a `device` attribute
    (the status coordinator and the log coordinator both do).
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator=coordinator)
        device: SmartSolityDevice = coordinator.device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.nickname,
            manufacturer=MANUFACTURER,
            model=device.model_name,
        )
