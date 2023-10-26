"""Test nctalkbot integration."""
from homeassistant import config_entries, data_entry_flow
from homeassistant.config import async_process_ha_core_config
from homeassistant.core import HomeAssistant, callback
from homeassistant.setup import async_setup_component

from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN

from pytest_homeassistant_custom_component.typing import ClientSessionGenerator
from custom_components.nctalkbot.const import DOMAIN, EVENT_RECEIVED


async def test_setup(hass: HomeAssistant, config):
    """Test setting up nctalkbot integration."""
    assert await async_setup_component(hass, NOTIFY_DOMAIN, config)

    await hass.async_block_till_done()

    assert hass.services.has_service(NOTIFY_DOMAIN, DOMAIN) is True


async def test_config_flow_registers_webhook(
    hass: HomeAssistant,
    config_data,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """Test setting up integration and sending webhook."""
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://hass.local:8123"},
    )
    assert await async_setup_component(hass, "api", {"http": {}})
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == config_entries.SOURCE_USER
    assert result["handler"] == DOMAIN

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config_data
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    webhook_id = result["result"].data["webhook_id"]

    events = []

    @callback
    def handle_event(event):
        """Handle event."""
        events.append(event)

    hass.bus.async_listen(EVENT_RECEIVED, handle_event)

    client = await hass_client_no_auth()
    await client.post(f"/api/webhook/{webhook_id}", json={"hello": DOMAIN})

    assert len(events) == 1
    assert events[0].data["webhook_id"] == webhook_id
    assert events[0].data["hello"] == DOMAIN

    # Invalid JSON
    await client.post(f"/api/webhook/{webhook_id}", data="not a dict")
    assert len(events) == 1

    # Not a dict
    await client.post(f"/api/webhook/{webhook_id}", json="not a dict")
    assert len(events) == 1


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
    assert result["step_id"] == config_entries.SOURCE_USER
    assert result["handler"] == DOMAIN

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config_data
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == DOMAIN
