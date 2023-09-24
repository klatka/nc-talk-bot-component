"""Tests for the nctalkbot integration."""
import pytest

from homeassistant.const import CONF_PLATFORM, CONF_NAME, CONF_URL
from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN

from custom_components.nctalkbot.const import (
    DOMAIN,
    CONF_ROOM_TOKEN,
    CONF_SHARED_SECRET,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def config():
    """Fixture for a nctalkbot configuration."""
    return {
        NOTIFY_DOMAIN: [
            {
                CONF_PLATFORM: DOMAIN,
                CONF_NAME: "nctalkbot",
                CONF_URL: "https://test",
                CONF_SHARED_SECRET: "test_secret",
                CONF_ROOM_TOKEN: "test_token",
            }
        ]
    }
