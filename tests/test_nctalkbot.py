"""Test nctalkbot integration."""
from homeassistant.setup import async_setup_component

from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN
from custom_components.nctalkbot.const import DOMAIN


async def test_setup(hass, config):
    """Test setting up nctalkbot integration."""
    assert await async_setup_component(hass, NOTIFY_DOMAIN, config)

    await hass.async_block_till_done()

    assert hass.services.has_service(NOTIFY_DOMAIN, DOMAIN) is True
