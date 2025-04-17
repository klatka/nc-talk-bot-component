"""Config flow for the integration."""

from __future__ import annotations

import logging
from typing import Any
import secrets

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_WEBHOOK_ID
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.components import webhook

from .const import (
    DOMAIN,
    CONF_SHARED_SECRET,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
    }
)


async def validate_config(data: dict[str, Any]):
    """Validate the user input."""
    if not data[CONF_URL]:
        raise ValueError("URL not given")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._url: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a user initiated set up flow to create a webhook."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors = {}

        if user_input is not None:
            try:
                await validate_config(user_input)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("User input invalid %s", user_input)
                errors["base"] = "User input invalid"
            else:
                self._url = user_input[CONF_URL]
                return await self.async_step_webhook(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_webhook(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the webhook setup step."""
        if user_input is None:
            return self.async_show_form(step_id="webhook")

        webhook_id = webhook.async_generate_id()
        shared_secret = secrets.token_hex(64)

        return self.async_create_entry(
            title=DOMAIN,
            data={
                CONF_WEBHOOK_ID: webhook_id,
                CONF_SHARED_SECRET: shared_secret,
                CONF_URL: self._url,
            },
        )
