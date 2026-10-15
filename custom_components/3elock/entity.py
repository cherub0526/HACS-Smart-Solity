"""Base entity for the 3elock integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SmartSolityDataUpdateCoordinator


class SmartSolityEntity(CoordinatorEntity[SmartSolityDataUpdateCoordinator]):
    """Base entity for a lock device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SmartSolityDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator=coordinator)
        device = coordinator.device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.nickname,
            manufacturer=MANUFACTURER,
            model=device.model_name,
        )
