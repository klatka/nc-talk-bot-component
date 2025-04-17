"""Test nctalkbot integration."""

from homeassistant import config_entries, data_entry_flow
from homeassistant.config import async_process_ha_core_config
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN

from custom_components.nctalkbot.const import DOMAIN, CONF_URL, CONF_SHARED_SECRET, CONF_WEBHOOK_ID


async def test_setup(hass: HomeAssistant, config):
    """Test setting up nctalkbot integration."""
    assert await async_setup_component(hass, NOTIFY_DOMAIN, config)

    await hass.async_block_till_done()

    assert hass.services.has_service(NOTIFY_DOMAIN, DOMAIN) is True


async def test_flow_manual_configuration(hass: HomeAssistant, config_data):
    """Test that config flow works."""
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://hass.local:8123"},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["handler"] == DOMAIN

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_URL: config_data[CONF_URL]}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == DOMAIN
    assert result["data"][CONF_URL] == config_data[CONF_URL]
    assert result["data"][CONF_SHARED_SECRET] is not None
    assert result["data"][CONF_WEBHOOK_ID] is not None
