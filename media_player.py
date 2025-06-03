from __future__ import annotations

import logging
import aiohttp

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_NAME
from datetime import datetime, timezone, timedelta

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    DEFAULT_NAME,
    CONF_APP_TOKEN,
    CONF_USE_SSL,
    CONF_PORT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Cider Media Player platform."""
    session = async_get_clientsession(hass)
    host = entry.data[CONF_HOST]
    app_token = entry.data[CONF_APP_TOKEN]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    use_ssl = entry.data.get(CONF_USE_SSL, False)
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    async_add_entities([CiderMediaPlayer(session, host, port, app_token, use_ssl, name)], True)

class CiderMediaPlayer(MediaPlayerEntity):
    """Representation of a Cider Media Player."""

    _attr_has_entity_name = True
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_should_poll = True  # Add this line
    _attr_media_content_type = "music"

    def __init__(self, session: aiohttp.ClientSession, host: str, port: str, app_token: str, use_ssl: bool = False, name: str = DEFAULT_NAME) -> None:
        """Initialize the media player."""
        self._session = session
        self._host = host
        self._port = port
        self._app_token = app_token
        self._headers = {"apptoken": app_token}
        protocol = "https" if use_ssl else "http"
        self._base_url = f"{protocol}://{host}:{port}/api/v1/playback"
        self._attr_unique_id = f"{DOMAIN}_{name}"
        self._attr_name = name
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
            | MediaPlayerEntityFeature.SEEK
            | MediaPlayerEntityFeature.VOLUME_MUTE
            # | MediaPlayerEntityFeature.SELECT_SOURCE
            # | MediaPlayerEntityFeature.BROWSE_MEDIA
            # | MediaPlayerEntityFeature.PLAY_MEDIA
            # | MediaPlayerEntityFeature.SELECT_SOUND_MODE
            # | MediaPlayerEntityFeature.SHUFFLE_SET
            # | MediaPlayerEntityFeature.REPEAT_SET
        )

    async def _async_api_call(self, method: str, endpoint: str, data: dict | None = None) -> tuple[bool, dict]:
        """Make an API call and handle errors."""
        try:
            kwargs = {"headers": self._headers}
            if method == "post" and data is not None:
                kwargs["json"] = data

            async with getattr(self._session, method)(f"{self._base_url}/{endpoint}", **kwargs) as response:
                if response.status == 200:
                    return True, await response.json() if method == "get" else {}
                _LOGGER.debug("API call failed with status %s: %s", response.status, await response.text())
                return False, {}
        except aiohttp.ClientError as error:
            _LOGGER.debug("Failed to call %s: %s", endpoint, error)
            self._attr_state = MediaPlayerState.OFF
            return False, {}

    async def async_update(self) -> None:
        """Fetch latest state."""
        # Update playing state
        success, data = await self._async_api_call("get", "is-playing")
        if success:
            self._attr_state = (
                MediaPlayerState.PLAYING if bool(data.get("is_playing"))
                else MediaPlayerState.PAUSED
            )

        # Update volume
        success, data = await self._async_api_call("get", "volume")
        if success:
            self._attr_volume_level = float(data.get("volume", 0))

        # Update current song info
        success, data = await self._async_api_call("get", "now-playing")
        if success:
            info = data.get("info", {})
            artwork = info.get("artwork", {})
            self._attr_media_title = info.get("name", "")
            self._attr_media_artist = info.get("artistName", "")
            self._attr_media_album_name = info.get("albumName", "")
            self._attr_media_album_artist = info.get("artistName", "")
            self._attr_media_image_url = artwork.get("url") if artwork else None
            self._attr_media_duration = info.get("durationInMillis", 0) / 1000
            self._attr_media_position = info.get("currentPlaybackTime", 0) / 1000
            self._attr_media_position_updated_at = datetime.now(timezone.utc) - timedelta(seconds=info.get("currentPlaybackTime", 0))


    async def async_media_play(self) -> None:
        """send play command."""
        success, _ = await self._async_api_call("post", "play", data={})
        if success:
            self._attr_state = MediaPlayerState.PLAYING

    async def async_media_pause(self) -> None:
        """send pause command."""
        success, _ = await self._async_api_call("post", "pause", data={})
        if success:
            self._attr_state = MediaPlayerState.PAUSED

    async def async_media_stop(self) -> None:
        """send stop command."""
        success, _ = await self._async_api_call("post", "stop", data={})
        if success:
            self._attr_state = MediaPlayerState.IDLE

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self._async_api_call("post", "next", data={})

    async def async_media_previous_track(self) -> None:
        """Send previous track command."""
        await self._async_api_call("post", "previous", data={})

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        success, _ = await self._async_api_call("post", "volume", data={"volume": volume})
        if success:
            self._attr_volume_level = volume

    async def async_media_seek(self, position: float) -> None:
        """Seek to position."""
        await self._async_api_call("post", "seek", data={"position": position})
