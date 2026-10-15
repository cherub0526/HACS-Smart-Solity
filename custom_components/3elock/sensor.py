"""Sensor platform for the 3elock integration."""

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
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SmartSolityConfigEntry, SmartSolityDataUpdateCoordinator
from .entity import SmartSolityEntity


@dataclass(frozen=True, kw_only=True)
class SmartSolitySensorDescription(SensorEntityDescription):
    """Describes a sensor derived from a myDevice field."""

    value_fn: Callable[[dict[str, Any]], Any]


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


SENSORS: tuple[SmartSolitySensorDescription, ...] = (
    SmartSolitySensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _int(d.get("battery")),
    ),
    SmartSolitySensorDescription(
        key="firmware_version",
        translation_key="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("fwVersion") or None,
    ),
    SmartSolitySensorDescription(
        key="connection_type",
        translation_key="connection_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("brokerType") or None,
    ),
    SmartSolitySensorDescription(
        key="security_level",
        translation_key="security_level",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _int(d.get("securitySetStatus")),
    ),
    SmartSolitySensorDescription(
        key="sound_level",
        translation_key="sound_level",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _int(d.get("soundSetStatus")),
    ),
    SmartSolitySensorDescription(
        key="voice_level",
        translation_key="voice_level",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _int(d.get("voiceSetStatus")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SmartSolityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    coordinator = config_entry.runtime_data.status
    async_add_entities(
        SmartSolitySensor(coordinator, description) for description in SENSORS
    )


class SmartSolitySensor(SmartSolityEntity, SensorEntity):
    """A single value read from the myDevice record."""

    entity_description: SmartSolitySensorDescription

    def __init__(
        self,
        coordinator: SmartSolityDataUpdateCoordinator,
        description: SmartSolitySensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device.device_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
