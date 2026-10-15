"""Config flow for the 3elock integration (PIN or email login)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
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

PIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)

EMAIL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
        ),
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
        self, identifier: str, password: str
    ) -> tuple[SmartSolityDevice | None, str | None]:
        """Validate credentials against the API."""
        api = SmartSolityApiClient(
            async_get_clientsession(self.hass), identifier, password
        )
        try:
            await api.login()
            device = await api.get_my_device()
        except SmartSolityAuthError:
            return None, "invalid_auth"
        except (SmartSolityApiError, SmartSolityConnectionError):
            return None, "cannot_connect"
        return device, None

    async def _async_finish(
        self, identifier: str, password: str
    ) -> ConfigFlowResult | str:
        """Validate, set unique id and create the entry, or return an error key."""
        device, error = await self._async_validate(identifier, password)
        if error is not None:
            return error
        assert device is not None
        await self.async_set_unique_id(device.device_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=device.nickname,
            data={CONF_USERNAME: identifier, CONF_PASSWORD: password},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick a login method."""
        return self.async_show_menu(step_id="user", menu_options=["pin", "email"])

    async def async_step_pin(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Log in with the 6-digit app password (used as id and password)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            pin = user_input[CONF_PASSWORD]
            result = await self._async_finish(pin, pin)
            if isinstance(result, str):
                errors["base"] = result
            else:
                return result
        return self.async_show_form(
            step_id="pin", data_schema=PIN_SCHEMA, errors=errors
        )

    async def async_step_email(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Log in with an account email + password."""
        errors: dict[str, str] = {}
        if user_input is not None:
            result = await self._async_finish(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if isinstance(result, str):
                errors["base"] = result
            else:
                return result
        return self.async_show_form(
            step_id="email", data_schema=EMAIL_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth triggered by ConfigEntryAuthFailed."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Re-enter credentials for the same device, in the original mode."""
        entry = self._get_reauth_entry()
        is_pin = entry.data[CONF_USERNAME] == entry.data[CONF_PASSWORD]
        errors: dict[str, str] = {}
        if user_input is not None:
            if is_pin:
                identifier = password = user_input[CONF_PASSWORD]
            else:
                identifier = user_input[CONF_USERNAME]
                password = user_input[CONF_PASSWORD]
            device, error = await self._async_validate(identifier, password)
            if error is not None:
                errors["base"] = error
            else:
                assert device is not None
                await self.async_set_unique_id(device.device_id)
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_USERNAME: identifier,
                        CONF_PASSWORD: password,
                    },
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=PIN_SCHEMA if is_pin else EMAIL_SCHEMA,
            errors=errors,
        )
