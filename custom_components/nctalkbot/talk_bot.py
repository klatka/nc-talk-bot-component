"""Nextcloud Talk Bot class."""
import logging
import hashlib
import hmac

from random import choice
from string import ascii_lowercase, ascii_uppercase, digits

import httpx

_LOGGER = logging.getLogger(__name__)

class TalkBot:
    """A class that implements the TalkBot functionality."""

    def __init__(self, nc_url: str, shared_secret: str = ""):
        """Class implementing Nextcloud Talk Bot functionality."""
        self.nc_url = nc_url
        self.shared_secret = shared_secret

    async def async_send_message(
        self, message: str, token: str = ""
    ) -> httpx.Response:
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

        return await self._async_sign_send_request(
            f"/{token}/message", params, message
        )

    async def _async_sign_send_request(
        self, url_suffix: str, data: dict, data_to_sign: str
    ) -> httpx.Response:
        talk_bot_random = self._random_string(32)
        hmac_sign = self.sign_data(
            data_to_sign, self.shared_secret, talk_bot_random
        )
        headers = {
            "X-Nextcloud-Talk-Bot-Random": talk_bot_random,
            "X-Nextcloud-Talk-Bot-Signature": hmac_sign.hexdigest(),
            "OCS-APIRequest": "true",
        }
        url = self.nc_url + "/ocs/v2.php/apps/spreed/api/v1/bot" + url_suffix

        _LOGGER.debug("Sending %s with header %s to %s", hmac_sign, headers, url)

        async with httpx.AsyncClient() as client:
            r = await client.post(
                url=url,
                json=data,
                headers=headers,
            )

        return r

    def sign_data(self, data_to_sign: str, secret: str, random: str) -> hmac.HMAC:
        """Sign data with the given secret and return the HMAC."""
        hmac_sign = hmac.new(
            secret.encode("UTF-8"),
            random.encode("UTF-8"),
            digestmod=hashlib.sha256,
        )
        hmac_sign.update(data_to_sign.encode("UTF-8"))
        return hmac_sign

    def _random_string(self, size: int) -> str:
        """Generates a random ASCII string of the given size."""

        letters = ascii_lowercase + ascii_uppercase + digits
        return "".join(choice(letters) for _ in range(size))
