"""Config flow for the 3elock integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    SmartSolityApiClient,
    SmartSolityApiError,
    SmartSolityAuthError,
    SmartSolityConnectionError,
    SmartSolityDevice,
)
from .const import DOMAIN

STEP_PASSWORD_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


class SmartSolityConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 3elock."""

    async def _async_validate(
        self, password: str
    ) -> tuple[SmartSolityDevice | None, str | None]:
        """Validate the 6-digit app password against the API."""
        api = SmartSolityApiClient(async_get_clientsession(self.hass), password)
        try:
            await api.login()
            device = await api.get_my_device()
        except SmartSolityAuthError:
            return None, "invalid_auth"
        except (SmartSolityApiError, SmartSolityConnectionError):
            return None, "cannot_connect"
        return device, None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            device, error = await self._async_validate(user_input[CONF_PASSWORD])
            if error is None:
                assert device is not None
                await self.async_set_unique_id(device.device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=device.nickname, data=user_input)
            errors["base"] = error

        return self.async_show_form(
            step_id="user", data_schema=STEP_PASSWORD_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth triggered by ConfigEntryAuthFailed."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the reauth confirmation step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            device, error = await self._async_validate(user_input[CONF_PASSWORD])
            if error is None:
                assert device is not None
                await self.async_set_unique_id(device.device_id)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates=user_input
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_PASSWORD_SCHEMA,
            errors=errors,
        )
