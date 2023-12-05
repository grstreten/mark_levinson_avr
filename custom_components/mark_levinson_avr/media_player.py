"""Support for interface with an Harman/Kardon or JBL AVR."""
from __future__ import annotations

from .mlctrl import MLCtrl
import voluptuous as vol
from datetime import datetime, timedelta

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

DEFAULT_NAME = "Mark Levinson AVR"
DEFAULT_PORT = 15003
SCAN_INTERVAL = timedelta(seconds=4)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discover_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the AVR platform."""
    name = config[CONF_NAME]
    host = config[CONF_HOST]
    port = config[CONF_PORT]

    avr = MLCtrl(host, port, name)
    avr_device = MLAvrDevice(avr)

    add_entities([avr_device], True)


class MLAvrDevice(MediaPlayerEntity):
    """Representation of a Mark Levinson AVR/Pre-Amplifier."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, avr):
        """Initialize a new MarkLevinsonAVR."""
        self._avr = avr

        self._name = avr.name
        self._host = avr.host
        self._port = avr.port

        self._source_list = avr.sources

        self._volume = avr.volume / 100 if avr.volume else 0.0

        self._muted = avr.muted
        self._current_source = avr.current_source

    def update(self) -> None:
        """Update the state of this media_player."""

        self._avr.update_all()

        if self._avr.is_on():
            self._attr_state = MediaPlayerState.ON
        elif self._avr.is_off():
            self._attr_state = MediaPlayerState.OFF
        else:
            self._attr_state = None

        self._volume = self._avr.volume / 100 if self._avr.volume else 0.0
        self._muted = self._avr.muted
        self._current_source = self._avr.current_source

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def is_volume_muted(self):
        """Muted status not available."""
        return self._muted

    @property
    def source(self):
        """Return the current input source."""
        return self._current_source

    @property
    def source_list(self):
        """Available sources."""
        return self._source_list

    def turn_on(self) -> None:
        """Turn the AVR on."""
        self._avr.power_on()

    def turn_off(self) -> None:
        """Turn off the AVR."""
        self._avr.power_off()

    def select_source(self, source: str) -> None:
        """Select input source."""
        return self._avr.select_source(source)

    def volume_up(self) -> None:
        """Volume up the AVR."""
        return self._avr.volume_up()

    def volume_down(self) -> None:
        """Volume down AVR."""
        return self._avr.volume_down()

    def set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        return self._avr.set_volume(volume * 100)

    def mute_volume(self, mute: bool) -> None:
        """Send mute command."""
        return self._avr.mute(mute)
