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

from .const import CREDENTIAL_TYPES
from .coordinator import (
    SmartSolityConfigEntry,
    SmartSolityCredentialCoordinator,
    SmartSolityDataUpdateCoordinator,
)
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
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SmartSolityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    data = config_entry.runtime_data
    entities: list[SensorEntity] = [
        SmartSolitySensor(data.status, description) for description in SENSORS
    ]
    entities.append(SmartSolityCredentialsSensor(data.credentials))
    async_add_entities(entities)


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


class SmartSolityCredentialsSensor(SmartSolityEntity, SensorEntity):
    """Named credentials (passwords/cards/fingerprints/faces) as a read-only list.

    State is the total number of *named* credentials; the per-type lists are in
    the attributes. Credentials that exist on the lock but have no nickname set
    in the app do not appear here.
    """

    _attr_translation_key = "credentials"
    _attr_native_unit_of_measurement = "entries"

    def __init__(self, coordinator: SmartSolityCredentialCoordinator) -> None:
        """Initialize the credentials sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device.device_id}_credentials"

    @property
    def native_value(self) -> int:
        """Return the total number of named credentials."""
        data = self.coordinator.data or {}
        return sum(len(v) for v in data.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the named entries grouped by credential type."""
        data = self.coordinator.data or {}
        return {key: data.get(key, []) for key in CREDENTIAL_TYPES}
