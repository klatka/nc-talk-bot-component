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
    CONF_ROOM_DEFAULT,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_URL): cv.url,
        vol.Required(CONF_SHARED_SECRET): cv.string,
        vol.Optional(CONF_ROOM_DEFAULT): cv.string,
    }
)


async def async_get_service(
    hass: HomeAssistant,  # pylint: disable=unused-argument
    config: ConfigType,
    discovery_info: (  # pylint: disable=unused-argument
        DiscoveryInfoType | None  # pylint: disable=unused-argument
    ) = None,  # pylint: disable=unused-argument
) -> BaseNotificationService | None:
    """Return the notify service."""

    return TalkBotNotificationService(config)


class TalkBotNotificationService(BaseNotificationService):  # pylint: disable=abstract-method
    """Implementation of a notification service."""

    def __init__(self, config):
        """Initialize the service."""

        self.bot = TalkBot(config[CONF_URL], config[CONF_SHARED_SECRET])
        self.default_target_room = config.get(CONF_ROOM_DEFAULT)

    async def async_send_message(self, message="", **kwargs):
        """Send a message to Nextcloud Talk bot."""

        targets = kwargs.get("target")
        if not targets and self.default_target_room is not None:
            targets = {self.default_target_room}
        if not targets:
            _LOGGER.error("No targets specified. Default room not set")
        else:
            for target in targets:
                try:
                    reply_to = ""
                    silent = False
                    if isinstance(kwargs.get("data"), dict):
                        reply_to = kwargs["data"].get("reply_to", "")
                        silent = kwargs["data"].get("silent", False)

                    r = await self.bot.async_send_message(
                        message, target, reply_to, silent
                    )
                    if not r.status_code == 201:
                        _LOGGER.error(
                            "Nextcloud Talk Bot rejected the message."
                            + " Secret or room name may be wrong."
                            + " Status code when posting message: %d",
                            r.status_code,
                        )
                except Exception as e:  # pylint: disable=broad-except
                    _LOGGER.error("Error sending message: %s", e)
