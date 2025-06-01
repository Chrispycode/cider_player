"""Constants for the Cider Media Player integration."""
from homeassistant.const import Platform

DOMAIN = "cider_player"
PLATFORMS = [Platform.MEDIA_PLAYER]

DEFAULT_NAME = "Cider"
DEFAULT_PORT = "10767"
CONF_APP_TOKEN = "app_token"
CONF_USE_SSL = "use_ssl"
CONF_PORT = "port"
