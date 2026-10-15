"""Constants for the 3elock (Smart Solity) integration."""

from __future__ import annotations

from datetime import timedelta
import logging

DOMAIN = "3elock"
MANUFACTURER = "Solity"
LOGGER = logging.getLogger(__package__)

# The app polls frequently; the server answers 304 when nothing changed.
UPDATE_INTERVAL = timedelta(seconds=5)
