from __future__ import annotations

import logging
import asyncio
import aiohttp
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    DEFAULT_PORT,
    CONF_APP_TOKEN,
    CONF_USE_SSL,
    CONF_PORT,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_APP_TOKEN): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_USE_SSL, default=False): bool,
    }
)


async def validate_input(host: str, app_token: str, port: str, use_ssl: bool) -> bool:
    """Validate the user input allows us to connect."""
    try:
        async with aiohttp.ClientSession() as session:
            protocol = "https" if use_ssl else "http"
            async with session.get(
                f"{protocol}://{host}:{port}/api/v1/playback/active",
                timeout=aiohttp.ClientTimeout(total=5),
                headers={"apptoken": app_token}
            ) as response:
                _LOGGER.debug("Connection test response: %s", response.status)
                return response.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        _LOGGER.error("Connection test failed: %s", str(err))
        return False
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error during connection test: %s", str(err))
        return False


class CiderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cider Media Player."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                valid = await validate_input(
                    user_input[CONF_HOST],
                    user_input[CONF_APP_TOKEN],
                    user_input.get(CONF_PORT, DEFAULT_PORT),
                    user_input.get(CONF_USE_SSL, False)
                )
                if valid:
                    # Check if this host is already configured
                    await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_HOST]}")
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME, DEFAULT_NAME),
                        data={
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_APP_TOKEN: user_input[CONF_APP_TOKEN],
                            CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                            CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                            CONF_USE_SSL: user_input.get(CONF_USE_SSL, False),
                        },
                    )
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", str(err))
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

