"""Event platform for the 3elock integration.

Turns the Solity access log (retrieveLog) into Home Assistant events: each new
log entry fires an event, categorized as unlock / lock / user / other, with the
original message and metadata as event attributes.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SmartSolityConfigEntry, SmartSolityLogCoordinator
from .entity import SmartSolityEntity

EVENT_UNLOCK = "unlock"
EVENT_LOCK = "lock"
EVENT_USER = "user"
EVENT_OTHER = "other"
EVENT_TYPES = [EVENT_UNLOCK, EVENT_LOCK, EVENT_USER, EVENT_OTHER]


def _categorize(log: dict[str, Any]) -> str:
    """Map a raw log entry to one of the fixed event types."""
    code = str(log.get("logMsgCd") or "")
    log_type = str(log.get("logType") or "")
    if code.startswith("bleLog.open") or code.startswith("bleLog.in"):
        return EVENT_UNLOCK
    if code.startswith("bleLog.close") or code.startswith("bleLog.lock"):
        return EVENT_LOCK
    if log_type == "USER_EVENT" or code.startswith("myDeviceUser"):
        return EVENT_USER
    return EVENT_OTHER


def _key(log: dict[str, Any]) -> tuple[Any, Any, Any]:
    """A stable identity for a log entry (to detect new ones)."""
    return (log.get("logDateTime"), log.get("logMsgCd"), log.get("logMessage"))


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SmartSolityConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the activity event entity."""
    async_add_entities([SmartSolityActivityEvent(config_entry.runtime_data.logs)])


class SmartSolityActivityEvent(SmartSolityEntity, EventEntity):
    """Fires an event for each new access-log entry."""

    _attr_translation_key = "activity"
    _attr_event_types = EVENT_TYPES

    def __init__(self, coordinator: SmartSolityLogCoordinator) -> None:
        """Initialize the event entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device.device_id}_activity"
        self._last_key: tuple[Any, Any, Any] | None = None

    async def async_added_to_hass(self) -> None:
        """Mark the newest existing entry as seen, then listen for new ones."""
        await super().async_added_to_hass()
        logs = self.coordinator.data or []
        if logs:
            self._last_key = _key(logs[0])
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        """Fire an event for every entry newer than the last one seen."""
        logs = self.coordinator.data or []
        if not logs:
            return
        new: list[dict[str, Any]] = []
        for log in logs:  # newest first
            if self._last_key is not None and _key(log) == self._last_key:
                break
            new.append(log)
        if not new:
            return
        self._last_key = _key(logs[0])
        for log in reversed(new):  # fire oldest-first
            self._trigger_event(
                _categorize(log),
                {
                    "message": log.get("logMessage"),
                    "time": log.get("logDateTime"),
                    "log_type": log.get("logType"),
                    "log_code": log.get("logCode"),
                    "media_type": log.get("mediaType"),
                    "msg_code": log.get("logMsgCd"),
                    "member": log.get("memberName"),
                },
            )
            self.async_write_ha_state()
