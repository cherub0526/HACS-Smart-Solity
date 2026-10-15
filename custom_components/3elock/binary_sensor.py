"""Binary sensor platform for the 3elock integration.

Exposes the lock's door status plus the various on/off setting flags from
the myDevice record. Flag values are "0"/"1" or "N"/"Y"; both map to off/on.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SmartSolityConfigEntry, SmartSolityDataUpdateCoordinator
from .entity import SmartSolityEntity

_ON = {"Y", "1"}
_OFF = {"N", "0"}


def _flag(dev: dict[str, Any], key: str) -> bool | None:
    """Interpret a Y/N or 1/0 flag as on/off."""
    value = dev.get(key)
    text = str(value).strip().upper() if value is not None else ""
    if text in _ON:
        return True
    if text in _OFF:
        return False
    return None


@dataclass(frozen=True, kw_only=True)
class SmartSolityBinaryDescription(BinarySensorEntityDescription):
    """Describes a binary sensor derived from a myDevice field."""

    value_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSORS: tuple[SmartSolityBinaryDescription, ...] = (
    # Door status: BinarySensorDeviceClass.LOCK -> on = unlocked, off = locked.
    # lockerStatus == "0" means locked.
    SmartSolityBinaryDescription(
        key="lock_state",
        translation_key="lock_state",
        device_class=BinarySensorDeviceClass.LOCK,
        value_fn=lambda d: d.get("lockerStatus") != "0",
    ),
    SmartSolityBinaryDescription(
        key="gateway",
        translation_key="gateway",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _flag(d, "gatewayConnStatus"),
    ),
    SmartSolityBinaryDescription(
        key="firmware_update",
        translation_key="firmware_update",
        device_class=BinarySensorDeviceClass.UPDATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _flag(d, "firmwareUpdateNeedYn"),
    ),
    SmartSolityBinaryDescription(
        key="keep_open",
        translation_key="keep_open",
        value_fn=lambda d: _flag(d, "keepOpenSetStatus"),
    ),
    SmartSolityBinaryDescription(
        key="auto_lock",
        translation_key="auto_lock",
        value_fn=lambda d: _flag(d, "lockTimeSetStatus"),
    ),
    SmartSolityBinaryDescription(
        key="dual_auth",
        translation_key="dual_auth",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _flag(d, "dualAuthSetStatus"),
    ),
    SmartSolityBinaryDescription(
        key="double_close",
        translation_key="double_close",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _flag(d, "doubleCloseSetStatus"),
    ),
    SmartSolityBinaryDescription(
        key="buzzer",
        translation_key="buzzer",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _flag(d, "buzzerUseStatus"),
    ),
    SmartSolityBinaryDescription(
        key="fake_number",
        translation_key="fake_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _flag(d, "fakeNumberSetStatus"),
    ),
    SmartSolityBinaryDescription(
        key="sublatch",
        translation_key="sublatch",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _flag(d, "sublatchSetStatus"),
    ),
    SmartSolityBinaryDescription(
        key="event_notification",
        translation_key="event_notification",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _flag(d, "notiDoorEventSetStatus"),
    ),
    SmartSolityBinaryDescription(
        key="status_notification",
        translation_key="status_notification",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _flag(d, "notiDoorStatusSetStatus"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SmartSolityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensors."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        SmartSolityBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class SmartSolityBinarySensor(SmartSolityEntity, BinarySensorEntity):
    """A single on/off flag read from the myDevice record."""

    entity_description: SmartSolityBinaryDescription

    def __init__(
        self,
        coordinator: SmartSolityDataUpdateCoordinator,
        description: SmartSolityBinaryDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device.device_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return the flag state."""
        return self.entity_description.value_fn(self.coordinator.data)
