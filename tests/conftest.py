"""Tests for the nctalkbot integration."""
import os
import sys
import pytest

from homeassistant.const import CONF_PLATFORM, CONF_NAME, CONF_URL
from homeassistant.components.notify import DOMAIN as NOTIFY_DOMAIN

from custom_components.nctalkbot.const import (
    DOMAIN,
    CONF_SHARED_SECRET,
    CONF_ROOM_DEFAULT,
)


if "HA_CLONE" in os.environ:
    # Rewire the testing package to the cloned test modules
    sys.modules["pytest_homeassistant_custom_component"] = __import__("tests")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
):  # pylint: disable=unused-argument
    """Enable custom integrations."""
    yield


@pytest.fixture
def config():
    """Fixture for a nctalkbot configuration."""
    return {
        NOTIFY_DOMAIN: [
            {
                CONF_PLATFORM: DOMAIN,
                CONF_NAME: "nctalkbot",
                CONF_URL: "https://test.local",
                CONF_SHARED_SECRET: "test_secret",
                CONF_ROOM_DEFAULT: "test_token",
            }
        ]
    }


@pytest.fixture
def config_data():
    """Fixture for a nctalkbot config flow."""
    return {
        CONF_URL: "https://test.local",
    }
