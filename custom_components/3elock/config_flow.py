"""Config flow for Smart Solity."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SmartSolityApi, SmartSolityAuthError, SmartSolityError
from .const import CONF_EMAIL, CONF_PASSWORD, DEFAULT_APP_SOURCE, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class SmartSolityConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Smart Solity config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = SmartSolityApi(
                session,
                email,
                user_input[CONF_PASSWORD],
                app_source=DEFAULT_APP_SOURCE,
            )
            try:
                await api.login()
            except SmartSolityAuthError:
                errors["base"] = "invalid_auth"
            except SmartSolityError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during Smart Solity login")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=email,
                    data={CONF_EMAIL: email, CONF_PASSWORD: user_input[CONF_PASSWORD]},
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
