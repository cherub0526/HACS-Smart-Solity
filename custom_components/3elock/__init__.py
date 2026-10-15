"""The 3elock (Smart Solity) integration."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .api import (
    SmartSolityApiClient,
    SmartSolityApiError,
    SmartSolityAuthError,
    SmartSolityConnectionError,
)
from .coordinator import (
    SmartSolityConfigEntry,
    SmartSolityDataUpdateCoordinator,
    SmartSolityLogCoordinator,
    SmartSolityRuntimeData,
)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.LOCK,
    Platform.SENSOR,
]


def _timezone_param(hass: HomeAssistant) -> str:
    """Build the pTimezone query value, e.g. '+8:00', from HA's local offset."""
    offset = dt_util.now().utcoffset()
    total = int(offset.total_seconds()) if offset else 0
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return f"{sign}{total // 3600}:{(total % 3600) // 60:02d}"


async def async_setup_entry(hass: HomeAssistant, entry: SmartSolityConfigEntry) -> bool:
    """Set up 3elock from a config entry."""
    api = SmartSolityApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    try:
        await api.login()
        device = await api.get_my_device()
    except SmartSolityAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except (SmartSolityApiError, SmartSolityConnectionError) as err:
        raise ConfigEntryNotReady(str(err)) from err

    status = SmartSolityDataUpdateCoordinator(hass, entry, api, device)
    logs = SmartSolityLogCoordinator(hass, entry, api, device, _timezone_param(hass))

    entry.runtime_data = SmartSolityRuntimeData(device=device, status=status, logs=logs)

    await status.async_config_entry_first_refresh()
    await logs.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SmartSolityConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
