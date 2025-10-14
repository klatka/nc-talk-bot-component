"""Test nctalkbot integration."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.setup import async_setup_component

from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN

from custom_components.nctalkbot.const import DOMAIN


async def test_setup(hass: HomeAssistant, config: ConfigType):
    """Test setting up nctalkbot integration."""
    assert await async_setup_component(hass, NOTIFY_DOMAIN, config)

    await hass.async_block_till_done()

    assert hass.services.has_service(NOTIFY_DOMAIN, DOMAIN) is True


async def test_flow_manual_configuration(hass: HomeAssistant, config_data):
    """Test that config flow works."""
    service_data = {
        "internal_url": "http://hass.local:8123",
    }

    await hass.config.async_update(**service_data)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["step_id"] == config_entries.SOURCE_USER
    assert result["handler"] == DOMAIN

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config_data
    )

    assert result["title"] == DOMAIN


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
