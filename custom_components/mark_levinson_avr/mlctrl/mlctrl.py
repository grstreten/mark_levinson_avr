#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the interface to Mark Levinson 502 Pre Amplifiers.

:copyright: (c) 2023 by George Streten, forked from Sander Geerts.
:license: MIT, see LICENSE for more details.
"""

import logging
import socket
import requests

_LOGGER = logging.getLogger("MLCtrl")

DEFAULT_SOURCES = []

COMMAND_MAPPING = {
    "POWER_OFF": "RQST:CS:PWR:STANDBY",
    "POWER_ON": "RQST:CS:PWR:ON",
    "SLEEP": "RQST:CS:PW:STANDBY",
    "VOLUME_UP": "RQST:CS:IRDWNUP:VOLUME_UP",
    "VOLUME_DOWN": "RQST:CS:IRDWNUP:VOLUME_DOWN",
    "VOLUME": "RQST:CS:VOL:",
    "MUTE_TOGGLE": "RQST:CS:MUTE:",
    "SOURCE": "RQST:CS:ACT:",
    "GET_SOURCES": "RQST:CS:REQ_ACT_LIST:?",
    "HEARTBEAT": "RQST:CS:PWR:?",
}

POWER_ON = "ON"
POWER_OFF = "OFF"
POWER_STANDBY = "STANDBY"
STATE_ON = "on"
STATE_OFF = "off"


class MLCtrl:
    """Representing a Harman Kardon AVR Device."""

    def __init__(self, host, port=15003, name=None):
        """
        Initialize MainZone of PreAmp.

        :param host: IP or HOSTNAME.
        :type host: str

        :param port: port.
        :type host: number

        :param name: Device name, if None FriendlyName of device is used.
        :type name: str or None
        """
        self._name = name
        self._host = host
        self._port = port
        # For now only support for main zone
        self._zone = "Main Zone"
        self._mute = STATE_OFF
        self._volume = -1.0

        self._state = None
        self._power = None
        self._current_source = None
        self._sources = DEFAULT_SOURCES

        self._socket = self._get_new_socket()

        self.update_all()

        print("Initialised, power is: " + self._power)

    def update_all(self):
        self.update_power_state()
        self.update_volume()
        self.update_mutestate()

        if self._power == POWER_ON:
            self.update_current_source()
            self.update_sources()

    def _get_new_socket(self):
        try:
            _new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _new_socket.connect((self._host, self._port))
            return _new_socket
        except ConnectionError as connection_error:
            _LOGGER.warning("Connection error: %s", connection_error)
            return None
        except socket.gaierror as socket_gaierror:
            _LOGGER.warning("Address-related error: %s", socket_gaierror)
            return None
        except socket.error as socket_error:
            _LOGGER.warning("Connection error: %s", socket_error)
            return None

    def _exec_appcommand_post(self, command, param):
        """Execute a command via HTTP POST."""
        try:
            if param:
                payload = command + param + "\r"
            else:
                payload = command + "\r"

            print("Q:   " + payload)
            self._socket.send(payload.encode())
            data = self._socket.recv(64)
            print("R:   " + data.decode("utf-8") + "\n")
            return data.decode("utf-8").replace("\r", "").replace("\n", "")
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: %s command not sent.", command)
            return False

    def send_command(self, command, param=""):
        comm = COMMAND_MAPPING[command]
        return self._exec_appcommand_post(comm, param)

    @property
    def sources(self):
        """
        Get sources list.
        """
        return self._sources

    @property
    def current_source(self):
        """
        Get the current source.
        """
        return self._current_source

    @property
    def zone(self):
        """Return Zone of this instance."""
        return self._zone

    @property
    def name(self):
        """Return the name of the device as string."""
        return self._name

    @property
    def host(self):
        """Return the host of the device as string."""
        return self._host

    @property
    def volume(self):
        """
        Return the volume of the device as float.
        """
        return str(self._volume)

    @property
    def power(self):
        """
        Return the power state of the device.
        Possible values are: "ON", "STANDBY" and "OFF"
        """
        return self._power

    @property
    def state(self):
        """
        Return the state of the device.

        Possible values are: "on", "off"
        """
        return self._state

    @property
    def muted(self):
        """
        Boolean if volume is currently muted.
        Return "True" if muted and "False" if not muted.
        """
        return bool(self._mute == STATE_ON)

    @property
    def port(self):
        """Return the receiver's port."""
        return self._port

    def is_on(self):
        return self._state == STATE_ON

    def is_off(self):
        return self._state == STATE_OFF

    def update_power_state(self):
        """Update the power state of the device."""
        try:
            resp = self.send_command("HEARTBEAT")
            if resp == "RSP:CS:PWR:STANDBY":
                self._power = POWER_STANDBY
                self._state = STATE_OFF
            elif resp == "RSP:CS:PWR:ON":
                self._power = POWER_ON
                self._state = STATE_ON
            elif resp == "RSP:CS:PWR:OFF":
                self._power = POWER_OFF
                self._state = STATE_OFF
            else:
                _LOGGER.error("Unknown power state: %s", resp)
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: power state not updated.")

    def update_sources(self):
        """Update the sources of the device."""
        try:
            resp = self.send_command("GET_SOURCES")
            if resp:
                if "RSP:CS:REQ_ACT_LIST:" in resp:
                    self._sources = resp.split(":")[3].split(",")
                else:
                    _LOGGER.error("Unknown sources: %s", resp)
            else:
                _LOGGER.error("Unknown sources: %s", resp)
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: sources not updated.")

    def update_current_source(self):
        """Update the current source of the device."""
        try:
            resp = self.send_command("SOURCE", "?")
            if resp:
                if "RSP:CS:ACT:" in resp:
                    if "ACK" in resp:
                        pass
                    elif "APROF" in resp:
                        pass
                        self.update_current_source()
                    else:
                        print(resp)
                        print(resp.split(":"))
                        print(resp.split(":")[3])
                        self._current_source = resp.split(":")[3]
                else:
                    _LOGGER.error("Unknown current source: %s", resp)
            else:
                _LOGGER.error("Unknown current source: %s", resp)
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: current source not updated.")

    def update_volume(self):
        """Update the volume of the device."""
        try:
            resp = self.send_command("VOLUME", "?")
            if resp:
                if "RSP:CS:VOL:" in resp or "NTF:UI:VOL:" in resp:
                    if "ACK" in resp:
                        pass
                    else:
                        try:
                            spl = resp.split(":")
                            self._volume = float(resp.split(":")[3])
                        except ValueError:
                            self._volume = -1.0
                else:
                    _LOGGER.error("Unknown volume: %s", resp)
            else:
                _LOGGER.error("Unknown volume: %s", resp)
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: volume not updated.")

    def update_mutestate(self):
        """Update the mute state of the device."""
        try:
            resp = self.send_command("MUTE_TOGGLE", "?")
            if resp:
                if "RSP:CS:MUTE:" in resp:
                    self._mute = resp.split(":")[3]
                else:
                    _LOGGER.error("Unknown mute state: %s", resp)
            else:
                _LOGGER.error("Unknown mute state: %s", resp)
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: mute state not updated.")

    def power_on(self):
        """Turn off receiver via command."""
        try:
            resp = self.send_command("POWER_ON")
            self._power = POWER_ON
            self._state = STATE_ON
            return True
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: power on command not sent.")
            return False

    def power_off(self):
        """Turn off receiver"""
        try:
            self.send_command("POWER_OFF")
            self._power = POWER_OFF
            self._state = STATE_OFF
            return True
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: power off command not sent.")
            return False

    def sleep(self):
        """Sleep"""
        try:
            self.send_command("SLEEP")
            return True
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: sleep command not sent.")
            return False

    def volume_up(self):
        """Volume up receiver"""
        try:
            new_vol = self._volume + 0.5
            self.set_volume(new_vol)
            return True
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: volume up command not sent.")
            return False

    def volume_down(self):
        """Volume down receiver"""
        try:
            new_vol = self._volume - 0.5
            self.set_volume(new_vol)
            return True
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: volume down command not sent.")
            return False

    def set_volume(self, volume):
        try:
            resp = self.send_command("VOLUME", str(volume))
            if "ACK" in resp:
                self._volume = float(volume)
                return True
            return True
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: volume down command not sent.")
            return False

    def select_source(self, source):
        try:
            self.send_command("SOURCE", source)
            resp = self._current_source = source
            if "ACK" in resp:
                self._current_source = source
                return True
            return True
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: select source command not sent.")
            return False

    def mute(self, mute):
        """Mute receiver"""
        try:
            if mute:
                self.send_command("MUTE_TOGGLE", "ON")
                self._mute = STATE_ON
                return True
            elif not mute:
                self.send_command("MUTE_TOGGLE", "OFF")
                self._mute = STATE_OFF
                return True
        except requests.exceptions.RequestException:
            _LOGGER.error("Connection error: mute command not sent.")
            return False

    def decode_message(self, message):
        message_components = message.split(":")

        HEADERS = {
            "RQST": "Request",
            "RSP": "Response",
            "NTF": "Broadcast Notification",
        }

        SOURCES = {"CS": "Control Source", "UI": "User Interaction", "AV": "Component"}

        COMMANDS = {
            "ACT": {
                "name": "Activity",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["Name"],
                "response": [],
            },
            "APROF": {
                "name": "Audio Profile",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["Name"],
                "response": ["Name"],
            },
            "AVSYNC": {
                "name": "Audio Video Sync Delay",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["0.0 - 500.0"],
                "response": ["0.0 - 500.0"],
            },
            "BAL": {
                "name": "Balance",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["ROFF", "LOFF", "-14.0 - 14.0"],
                "response": ["LOFF", "ROFF", "-14.0 - 14.0"],
            },
            "DISPCFG": {
                "name": "Display Configuration",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["Name"],
                "response": ["Name"],
            },
            "ENCENTER": {
                "name": "Center Channel",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["ON", "OFF"],
                "response": ["ON", "OFF"],
            },
            "ENSURR": {
                "name": "Surround Channel",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["ON", "OFF"],
                "response": ["ON", "OFF"],
            },
            "ENREAR": {
                "name": "Rear Channel",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["ON", "OFF"],
                "response": ["ON", "OFF"],
            },
            "ENSUB1": {
                "name": "Subwoofer 1",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["ON", "OFF"],
                "response": ["ON", "OFF"],
            },
            "ENSUB2": {
                "name": "Subwoofer 2",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["ON", "OFF"],
                "response": ["ON", "OFF"],
            },
            "FAULT": {
                "name": "Fault",
                "accepts_param": False,
                "accepts_query": False,
                "ack_on_set": False,
                "param_format": [],
                "response": ["THERM", "PWR", "SIGNAL", "UNKNOWN"],
            },
            "FPDISPINTENS": {
                "name": "Front Panel Display Intensity",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["OFF", "LOW", "MED", "HIGH"],
                "response": ["OFF", "LOW", "MED", "HIGH"],
            },
            "MONEN": {
                "name": "Monitor",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["ON", "OFF"],
                "response": ["ON", "OFF"],
            },
            "MUTE": {
                "name": "Mute",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["ON", "OFF"],
                "response": ["ON", "OFF"],
            },
            "NOP": {
                "name": "No Operation",
                "accepts_param": False,
                "accepts_query": False,
                "ack_on_set": True,
                "param_format": [],
                "response": [],
            },
            "PWR": {
                "name": "Power",
                "accepts_param": True,
                "accepts_query": True,
                "ack_on_set": True,
                "param_format": ["ON", "STANDBY"],
                "response": ["ON", "STANDBY"],
            },
            "REQ_ACT_LIST": {
                "name": "Request Activity List",
                "accepts_param": False,
                "accepts_query": True,
                "ack_on_set": False,
                "param_format": [],
                "response": ["Name List"],
            },
            "REQ_APROF_LIST": {
                "name": "Request Audio Profile List",
                "accepts_param": False,
                "accepts_query": True,
                "ack_on_set": False,
                "param_format": [],
                "response": ["Name List"],
            },
            "STATUS_MAIN": "Status",
            "STATUS_SYSTEM": "System Status",
            "SURRMODE": "Surround Mode",
            "TRIGGER_1": "Trigger 1",
            "TRIGGER_2": "Trigger 2",
            "TRIGGER_3": "Trigger 3",
            "TRIGGER_4": "Trigger 4",
            "VOL": "Volume",
            "VPROF": "Video Profile",
            "ZOOM": "Zoom",
        }

        header = message_components[0]
        source = message_components[1]
        command = message_components[2]
        param = message_components[3]
