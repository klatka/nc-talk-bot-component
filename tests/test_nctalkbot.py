"""Test nctalkbot integration."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from typing import cast
from aiohttp.web_request import Request

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.setup import async_setup_component
from homeassistant.const import CONF_URL, CONF_WEBHOOK_ID
from homeassistant.components.notify.const import DOMAIN as NOTIFY_DOMAIN

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)

from custom_components.nctalkbot import handle_webhook
from custom_components.nctalkbot.const import (
    DOMAIN,
    CONF_SHARED_SECRET,
    EVENT_RECEIVED,
)
from custom_components.nctalkbot.talk_bot import generate_signature, render_content


async def test_setup(hass: HomeAssistant, config: ConfigType):
    """Test setting up nctalkbot integration."""
    assert await async_setup_component(hass, NOTIFY_DOMAIN, config)

    await hass.async_block_till_done()

    assert hass.services.has_service(NOTIFY_DOMAIN, DOMAIN) is True


async def test_webhook_url_normalization():
    """Test that URL normalization works correctly for trailing slashes."""
    # Test 1: Both without trailing slash
    url1 = "https://test.local"
    server1 = "https://test.local"
    assert url1.rstrip("/") == server1.rstrip("/"), "Same URLs should match"

    # Test 2: Config without slash, server with slash
    url2 = "https://test.local"
    server2 = "https://test.local/"
    assert url2.rstrip("/") == server2.rstrip("/"), (
        "URLs with/without trailing slash should match"
    )

    # Test 3: Config with slash, server without slash
    url3 = "https://test.local/"
    server3 = "https://test.local"
    assert url3.rstrip("/") == server3.rstrip("/"), (
        "URLs with/without trailing slash should match"
    )

    # Test 4: Both with trailing slash
    url4 = "https://test.local/"
    server4 = "https://test.local/"
    assert url4.rstrip("/") == server4.rstrip("/"), (
        "Same URLs with slashes should match"
    )

    # Test 5: Different URLs should not match
    url5 = "https://test.local"
    server5 = "https://different.server"
    assert url5.rstrip("/") != server5.rstrip("/"), "Different URLs should not match"


async def test_config_entry_setup_registers_webhook(hass: HomeAssistant, config_data):
    """Ensure config entry setup registers the webhook."""
    entry = MockConfigEntry(domain=DOMAIN, data=config_data, title="nctalkbot")
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.nctalkbot.check_capability",
            AsyncMock(return_value=True),
        ) as mock_check_capability,
        patch("custom_components.nctalkbot.webhook.async_register") as mock_register,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    mock_check_capability.assert_awaited_once_with(config_data[CONF_URL], "bots-v1")
    mock_register.assert_called_once_with(
        hass,
        DOMAIN,
        DOMAIN,
        config_data[CONF_WEBHOOK_ID],
        handle_webhook,
        allowed_methods=["POST"],
    )


async def test_handle_webhook_success_fires_event(hass: HomeAssistant):
    """Validate webhook happy-path flow fires an event with rendered content."""
    secret = "secret"
    hass.data[DOMAIN] = {CONF_URL: "https://test.local", CONF_SHARED_SECRET: secret}
    events = async_capture_events(hass, EVENT_RECEIVED)

    random_token = "abc123"
    content = '{"message":"Hello {user}","parameters":{"user":{"name":"Bob"}}}'
    body = json.dumps({"object": {"content": content}})
    signature = generate_signature(body, secret, random_token).hexdigest()
    request = SimpleNamespace(
        headers={
            "X-NEXTCLOUD-TALK-BACKEND": "https://test.local/",
            "X-NEXTCLOUD-TALK-RANDOM": random_token,
            "X-NEXTCLOUD-TALK-SIGNATURE": signature,
        }
    )
    request.text = AsyncMock(return_value=body)

    # Cast to aiohttp Request for type checkers; the SimpleNamespace provides the needed attributes.
    response = await handle_webhook(hass, "hook-id", cast(Request, request))
    await hass.async_block_till_done()

    assert response.status == 200
    assert len(events) == 1
    assert events[0].data["webhook_id"] == "hook-id"
    assert events[0].data["rendered_content"] == "Hello Bob"


async def test_handle_webhook_missing_backend_header_returns_401(
    hass: HomeAssistant,
):
    """Ensure webhook rejects requests that miss required headers."""
    hass.data[DOMAIN] = {CONF_URL: "https://test.local", CONF_SHARED_SECRET: "secret"}
    request = SimpleNamespace(headers={})
    request.text = AsyncMock(return_value="{}")

    response = await handle_webhook(hass, "hook-id", cast(Request, request))

    assert response.status == 401


def test_render_content_replaces_placeholders():
    """render_content should substitute placeholders with parameter names."""
    content = '{"message":"Welcome {user}","parameters":{"user":{"name":"Alice"}}}'
    assert render_content(content) == "Welcome Alice"


def test_render_content_invalid_json():
    """Invalid JSON should return the fallback string."""
    assert render_content("not json") == "Invalid JSON content"
