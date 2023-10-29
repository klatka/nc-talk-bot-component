"""Nextcloud Talk Bot class."""
import logging
import hashlib
import hmac
import os
import secrets
import xml.etree.ElementTree as ET
import httpx

_LOGGER = logging.getLogger(__name__)


class TalkBot:
    """A class that implements the TalkBot functionality."""

    def __init__(self, nc_url: str, shared_secret: str = ""):
        """Class implementing Nextcloud Talk Bot functionality."""
        self.nc_url = nc_url
        self.shared_secret = shared_secret

    async def async_send_message(
        self,
        message: str,
        token: str = "",
        reply_to: str = "",
        silent: bool = False,
        timeout=5,
    ) -> httpx.Response:
        """Send a message and returns the response."""

        if not token:
            raise ValueError("Specify 'token' value.")

        reference_id = hashlib.sha256(os.urandom(16)).hexdigest()
        data = {
            "message": message,
            "referenceId": reference_id,
        }

        if reply_to:
            data["replyTo"] = reply_to

        if silent:
            data["silent"] = silent

        random = secrets.token_hex(32)
        hmac_sign = generate_signature(
            data["message"], self.shared_secret, random
        )
        headers = {
            "X-Nextcloud-Talk-Bot-Random": random,
            "X-Nextcloud-Talk-Bot-Signature": hmac_sign.hexdigest(),
            "OCS-APIRequest": "true",
        }
        url = (
            self.nc_url + f"/ocs/v2.php/apps/spreed/api/v1/bot/{token}/message"
        )

        _LOGGER.debug("Sending %s with header %s to %s", data, headers, url)

        async with httpx.AsyncClient() as client:
            r = await client.post(
                url=url,
                json=data,
                headers=headers,
                timeout=timeout,
            )

        return r


@staticmethod
async def check_capability(nc_url: str, capability: str, timeout=5):
    """Check if the server supports the given capability."""
    capabilities_url = nc_url + "/ocs/v1.php/cloud/capabilities"
    headers = {
        "OCS-APIRequest": "true",
    }

    async with httpx.AsyncClient() as client:
        r = await client.get(
            url=capabilities_url,
            headers=headers,
            timeout=timeout,
        )

    if r.status_code == 200:
        root = ET.fromstring(r.content)
        capabilities = root.find(".//capabilities")
        if capabilities is not None:
            for feature in capabilities.findall(".//element"):
                if feature.text == capability:
                    return True
    return False


@staticmethod
def generate_signature(data: str, secret: str, random: str) -> hmac.HMAC:
    """Sign data with the given secret and return the HMAC."""
    hmac_sign = hmac.new(
        secret.encode("UTF-8"),
        random.encode("UTF-8"),
        digestmod=hashlib.sha256,
    )
    hmac_sign.update(data.encode("UTF-8"))
    return hmac_sign
