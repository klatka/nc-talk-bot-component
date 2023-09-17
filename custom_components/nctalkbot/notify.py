"""Notification service."""
import logging
import hashlib
import hmac

from random import choice
from string import ascii_lowercase, ascii_uppercase, digits

import httpx
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.notify import (
    PLATFORM_SCHEMA,
    BaseNotificationService,
)
from homeassistant.const import CONF_URL
from .const import (
    DOMAIN,
    CONF_ROOM_TOKEN,
    CONF_SHARED_SECRET,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_URL): vol.Url(),
        vol.Required(CONF_SHARED_SECRET): cv.string,
        vol.Optional(CONF_ROOM_TOKEN): cv.string,
    }
)


def get_service(hass, config, discovery_info=None):
    """Return the notify service."""

    token = config.get(CONF_ROOM_TOKEN)
    secret = config.get(CONF_SHARED_SECRET)
    url = config.get(CONF_URL)

    try:
        return TalkBotNotificationService(url, token, secret)
    except:
        _LOGGER.warning("Config for Talk with NC Bot is invalid")

    return None


class TalkBotNotificationService(BaseNotificationService):
    """Implement the notification service."""

    def __init__(self, url, token, secret):
        """Initialize the service."""

        self.bot = TalkBot(url, secret)
        self.token = token

    def send_message(self, message="", **kwargs):
        """Send a message to NC Talk."""

        targets = kwargs.get("target")
        if not targets and not (self.token is None):
            targets = {self.token}
        if not targets:
            _LOGGER.error("Talk with NC Bot: no targets")
        else:
            for target in targets:
                req = self.bot.send_message(message, target)
                if not req.status_code == 201:
                    _LOGGER.error(
                        "Incorrect status code when posting message: %d",
                        req.status_code,
                    )


class TalkBot:
    """A class that implements the TalkBot functionality."""

    def __init__(self, nc_url: str, shared_secret: str = ""):
        """Class implementing Nextcloud Talk Bot functionality."""
        self.nc_url = nc_url
        self.shared_secret = shared_secret

    def send_message(self, message: str, token: str = "") -> httpx.Response:
        """Send a message and returns the response."""

        if not token:
            raise ValueError("Specify 'token' value.")
        reference_id = hashlib.sha256(
            self._random_string(32).encode("UTF-8")
        ).hexdigest()
        params = {
            "message": message,
            "referenceId": reference_id,
        }
        return (
            self._sign_send_request(
                "POST", f"/{token}/message", params, message
            ),
            reference_id,
        )

    def _sign_send_request(
        self, method: str, url_suffix: str, data: dict, data_to_sign: str
    ) -> httpx.Response:
        talk_bot_random = self._random_string(32)
        hmac_sign = hmac.new(
            self.shared_secret.encode('UTF-8'),
            talk_bot_random.encode("UTF-8"),
            digestmod=hashlib.sha256,
        )
        hmac_sign.update(data_to_sign.encode("UTF-8"))
        headers = {
            "X-Nextcloud-Talk-Bot-Random": talk_bot_random,
            "X-Nextcloud-Talk-Bot-Signature": hmac_sign.hexdigest(),
            "OCS-APIRequest": "true",
        }

        return httpx.request(
            method,
            url=self.nc_url
            + "/ocs/v2.php/apps/spreed/api/v1/bot"
            + url_suffix,
            json=data,
            headers=headers,
        )

    def _random_string(self, size: int) -> str:
        """Generates a random ASCII string of the given size."""

        letters = ascii_lowercase + ascii_uppercase + digits
        return "".join(choice(letters) for _ in range(size))
