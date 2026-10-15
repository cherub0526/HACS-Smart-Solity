"""The Smart Solity (cloud) integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SmartSolityApi
from .const import CONF_APP_SOURCE, CONF_EMAIL, CONF_PASSWORD, DEFAULT_APP_SOURCE, DOMAIN
from .coordinator import SmartSolityCoordinator

PLATFORMS: list[Platform] = [Platform.LOCK, Platform.SENSOR]

type SmartSolityConfigEntry = ConfigEntry[SmartSolityCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SmartSolityConfigEntry) -> bool:
    """Set up Smart Solity from a config entry."""
    session = async_get_clientsession(hass)
    api = SmartSolityApi(
        session,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        app_source=entry.options.get(CONF_APP_SOURCE, DEFAULT_APP_SOURCE),
        phone_token=entry.entry_id,
    )

    coordinator = SmartSolityCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SmartSolityConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: SmartSolityConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
