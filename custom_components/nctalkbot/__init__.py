"""The Nextcloud Talk Bot integration."""
from __future__ import annotations
import json
import logging

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_flow
from aiohttp.web import Request, Response

from .talk_bot import TalkBot
from .const import DOMAIN, CONF_SHARED_SECRET, EVENT_RECEIVED

_LOGGER = logging.getLogger(__name__)


async def handle_webhook(
    hass: HomeAssistant, webhook_id: str, request: Request
) -> Response:
    """Handle webhook callback."""
    assert hass is not None
    data = hass.data[DOMAIN]

    _LOGGER.debug(
        "Received webhook from Nextcloud Talk Bot id=%s, config=%s, headers=%s, body=%s",
        webhook_id,
        data,
        request.headers,
        request.text,
    )

    if webhook_id in data[CONF_WEBHOOK_ID]:
        return Response(status=410)

    url = data[CONF_URL]
    secret = data[CONF_SHARED_SECRET]
    bot = TalkBot(url, secret)

    server = request.headers.get("X-NEXTCLOUD-TALK-BACKEND")
    if server is None:
        _LOGGER.error(
            "Received invalid data from Nextcloud. Missing header: %s",
            "X-NEXTCLOUD-TALK-BACKEND",
        )
        return Response(status=401)
    random = request.headers.get("X-NEXTCLOUD-TALK-RANDOM")
    if random is None:
        _LOGGER.error(
            "Received invalid data from Nextcloud. Missing header: %s",
            "X-NEXTCLOUD-TALK-RANDOM",
        )
        return Response(status=401)
    signature = request.headers.get("X-NEXTCLOUD-TALK-SIGNATURE")
    if signature is None:
        _LOGGER.error(
            "Received invalid data from Nextcloud. Missing header: %s",
            "X-NEXTCLOUD-TALK-SIGNATURE",
        )
        return Response(status=401)

    if url != server:
        _LOGGER.error(
            "Error validating server: %s / %s",
            url,
            server,
        )
        return Response(status=401)

    body = await request.text()
    digest = bot.sign_data(body, secret, random)

    if digest != signature:
        _LOGGER.error(
            "Error validating signature: %s / %s",
            digest,
            signature,
        )
        return Response(status=401)

    try:
        data = json.loads(body) if body else {}
    except ValueError:
        _LOGGER.error(
            "Data needs to be formatted as JSON: %s",
            body,
        )
        return Response(status=400)

    if not isinstance(data, dict):
        _LOGGER.error(
            "Data needs to be a dictionary: %s",
            data,
        )
        return Response(status=400)

    hass.bus.async_fire(EVENT_RECEIVED, data)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the component."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = entry.data

    webhook.async_register(
        hass,
        DOMAIN,
        DOMAIN,
        entry.data[CONF_WEBHOOK_ID],
        handle_webhook,
        allowed_methods=["POST"],
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
    return True


async_remove_entry = config_entry_flow.webhook_async_remove_entry
