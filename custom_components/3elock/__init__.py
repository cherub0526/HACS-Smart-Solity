"""The 3elock (Smart Solity) integration."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    SmartSolityApiClient,
    SmartSolityApiError,
    SmartSolityAuthError,
    SmartSolityConnectionError,
)
from .coordinator import SmartSolityConfigEntry, SmartSolityDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: SmartSolityConfigEntry) -> bool:
    """Set up 3elock from a config entry."""
    api = SmartSolityApiClient(async_get_clientsession(hass), entry.data[CONF_PASSWORD])
    try:
        await api.login()
        device = await api.get_my_device()
    except SmartSolityAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except (SmartSolityApiError, SmartSolityConnectionError) as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = SmartSolityDataUpdateCoordinator(hass, entry, api, device)
    entry.runtime_data = coordinator
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SmartSolityConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
