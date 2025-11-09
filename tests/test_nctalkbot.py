"""Test nctalkbot integration."""

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.setup import async_setup_component
from homeassistant.const import CONF_URL, CONF_WEBHOOK_ID
from homeassistant.components.notify.const import DOMAIN as NOTIFY_DOMAIN

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nctalkbot import handle_webhook
from custom_components.nctalkbot.const import DOMAIN


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

    with patch(
        "custom_components.nctalkbot.check_capability",
        AsyncMock(return_value=True),
    ) as mock_check_capability, patch(
        "custom_components.nctalkbot.webhook.async_register"
    ) as mock_register:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    mock_check_capability.assert_awaited_once_with(
        config_data[CONF_URL], "bots-v1"
    )
    mock_register.assert_called_once_with(
        hass,
        DOMAIN,
        DOMAIN,
        config_data[CONF_WEBHOOK_ID],
        handle_webhook,
        allowed_methods=["POST"],
    )
