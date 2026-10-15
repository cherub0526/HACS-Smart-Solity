"""Sensor platform for the 3elock integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
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
from homeassistant.util import dt as dt_util

from .coordinator import (
    SmartSolityConfigEntry,
    SmartSolityDataUpdateCoordinator,
    SmartSolityLogCoordinator,
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
    data = config_entry.runtime_data
    entities: list[SensorEntity] = [
        SmartSolitySensor(data.status, description) for description in SENSORS
    ]
    entities.append(SmartSolityLastActivitySensor(data.logs))
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


def _parse_dt(value: str | None) -> datetime | None:
    """Parse 'YYYY-MM-DD HH:MM:SS' (already in HA local time) as aware."""
    if not value:
        return None
    try:
        naive = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None
    return naive.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)


class SmartSolityLastActivitySensor(SmartSolityEntity, SensorEntity):
    """Timestamp of the most recent access-log entry, with details in attributes."""

    _attr_translation_key = "last_activity"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: SmartSolityLogCoordinator) -> None:
        """Initialize the last-activity sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device.device_id}_last_activity"

    @property
    def _latest(self) -> dict[str, Any] | None:
        logs = self.coordinator.data or []
        return logs[0] if logs else None

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp of the most recent log entry."""
        latest = self._latest
        return _parse_dt(latest.get("logDateTime")) if latest else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details of the latest entry plus a list of recent entries."""
        latest = self._latest
        if latest is None:
            return {}
        return {
            "message": latest.get("logMessage"),
            "log_type": latest.get("logType"),
            "log_code": latest.get("logCode"),
            "media_type": latest.get("mediaType"),
            "member": latest.get("memberName"),
            "recent": [
                {
                    "time": log.get("logDateTime"),
                    "message": log.get("logMessage"),
                    "type": log.get("logType"),
                }
                for log in (self.coordinator.data or [])[:20]
            ],
        }
