#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Library for controlling a Mark Levinson 502 Pre Amp
:copyright: (c) 2023 by George Streten, forked from Sander Geerts.
:license: MIT, see LICENSE for more details.
"""

# Set default logging handler to avoid "No handler found" warnings.
import logging

# Import mlctrl module
from .mlctrl import MLCtrl

logging.getLogger(__name__).addHandler(logging.NullHandler())

__title__ = "mlctrl"
__version__ = "0.0.1"
