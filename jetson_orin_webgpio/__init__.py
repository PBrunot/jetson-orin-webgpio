"""
Jetson Orin Web GPIO Controller

A web-based GPIO control interface for NVIDIA Jetson Orin development boards.
Provides a user-friendly web interface to configure, read, and write GPIO pins
on the Jetson Orin's 40-pin header.
"""

__version__ = "1.0.0"
__author__ = "Pascal Brunot"
__email__ = "pascal@example.com"

from .app import GPIOController, app

__all__ = ["GPIOController", "app"]