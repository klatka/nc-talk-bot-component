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

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a user initiated set up flow to create a webhook."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors = {}

        if user_input is not None:
            description_placeholder = {}
            cloudhook = False
            shared_secret = secrets.token_hex(64)
            description_placeholder[CONF_SHARED_SECRET] = shared_secret

            webhook_id = self.hass.components.webhook.async_generate_id()

            if "cloud" in self.hass.config.components:
                try:
                    if self.hass.components.cloud.async_active_subscription():
                        if not self.hass.components.cloud.async_is_connected():
                            return self.async_abort(
                                reason="cloud_not_connected"
                            )

                        webhook_url = await self.hass.components.cloud.async_create_cloudhook(
                            webhook_id
                        )
                        cloudhook = True
                except AttributeError:
                    # probably replaced cloud component by custom integration
                    pass

            if not cloudhook:
                webhook_url = self.hass.components.webhook.async_generate_url(
                    webhook_id
                )

            description_placeholder["webhook_url"] = webhook_url

            try:
                await validate_config(user_input)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("User input invalid %s", user_input)
                errors["base"] = "User input invalid"

            if not errors:
                return self.async_create_entry(
                    title=DOMAIN,
                    data={
                        CONF_WEBHOOK_ID: webhook_id,
                        "cloudhook": cloudhook,
                        CONF_SHARED_SECRET: shared_secret,
                        CONF_URL: user_input[CONF_URL],
                    },
                    description_placeholders=description_placeholder,
                )

        return self.async_show_form(
            step_id=config_entries.SOURCE_USER,
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
