"""Base entity for Smart Solity devices."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartSolityCoordinator


class SmartSolityEntity(CoordinatorEntity[SmartSolityCoordinator]):
    """Common device wiring for all Smart Solity entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SmartSolityCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def device(self) -> dict[str, Any]:
        """Current snapshot of this device from the coordinator."""
        return self.coordinator.data.get(self._device_id, {})

    @property
    def available(self) -> bool:
        return super().available and self._device_id in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        dev = self.device
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=dev.get("myDeviceNickName") or dev.get("myDeviceModelName") or "Smart Solity",
            manufacturer=dev.get("myDeviceMakerName") or "Solity",
            model=dev.get("myDeviceModelName"),
            serial_number=dev.get("regDeviceSerialNo"),
            sw_version=dev.get("myDeviceFirmwareVersion"),
        )
