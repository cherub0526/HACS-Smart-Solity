"""Sensor platform for Smart Solity (battery, firmware, gateway link)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartSolityConfigEntry
from .entity import SmartSolityEntity


@dataclass(frozen=True, kw_only=True)
class SmartSolitySensorDescription(SensorEntityDescription):
    """Describes a sensor derived from a MyDeviceList field."""

    value_fn: Callable[[dict[str, Any]], Any]


def _battery(dev: dict[str, Any]) -> int | None:
    value = dev.get("battery")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


SENSORS: tuple[SmartSolitySensorDescription, ...] = (
    SmartSolitySensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_battery,
    ),
    SmartSolitySensorDescription(
        key="firmware",
        translation_key="firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda dev: dev.get("myDeviceFirmwareVersion"),
    ),
    SmartSolitySensorDescription(
        key="gateway",
        translation_key="gateway",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda dev: dev.get("gatewayConnStatus"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartSolityConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        SmartSolitySensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in SENSORS
    )


class SmartSolitySensor(SmartSolityEntity, SensorEntity):
    """A single diagnostic value read from the device snapshot."""

    entity_description: SmartSolitySensorDescription

    def __init__(self, coordinator, device_id: str, description: SmartSolitySensorDescription) -> None:
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.device)
