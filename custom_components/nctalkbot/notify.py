"""Notification service."""
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.notify import (
    PLATFORM_SCHEMA,
    BaseNotificationService,
)
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .talk_bot import TalkBot
from .const import (
    CONF_SHARED_SECRET,
    CONF_ROOM_TOKENS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_URL): cv.url,
        vol.Required(CONF_SHARED_SECRET): cv.string,
        vol.Optional(CONF_ROOM_TOKENS): cv.ensure_list(cv.string),
    }
)


async def async_get_service(
    hass: HomeAssistant,  # pylint: disable=unused-argument
    config: ConfigType,
    discovery_info: DiscoveryInfoType
    | None = None,  # pylint: disable=unused-argument
) -> BaseNotificationService | None:
    """Return the notify service."""

    return TalkBotNotificationService(config)


class TalkBotNotificationService(
    BaseNotificationService
):  # pylint: disable=abstract-method
    """Implementation of a notification service."""

    def __init__(self, config):
        """Initialize the service."""

        self.bot = TalkBot(
            config.get(CONF_URL), config.get(CONF_SHARED_SECRET)
        )
        self.token_list = config.get(CONF_ROOM_TOKENS)

    async def async_send_message(self, message="", **kwargs):
        """Send a message to Nextcloud Talk bot."""

        targets = kwargs.get("target")
        if not targets and isinstance(self.token_list, list):
            targets = self.token_list
        if not targets:
            _LOGGER.error("No targets")
        else:
            for target in targets:
                try:
                    r = await self.bot.async_send_message(message, target)
                    if not r.status_code == 201:
                        _LOGGER.error(
                            "Incorrect status code when posting message: %d",
                            r.status_code,
                        )
                except Exception as e:  # pylint: disable=broad-except
                    _LOGGER.error("Error sending message: %s", e)
