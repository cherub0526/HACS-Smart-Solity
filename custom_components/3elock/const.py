"""Constants for the 3elock (Smart Solity) integration."""

from __future__ import annotations

from datetime import timedelta
import logging

DOMAIN = "3elock"
MANUFACTURER = "Solity"
LOGGER = logging.getLogger(__package__)

# The app polls frequently; the server answers 304 when nothing changed.
UPDATE_INTERVAL = timedelta(seconds=5)

# The access log changes rarely and is a full (non-304) fetch, so poll slowly.
LOG_UPDATE_INTERVAL = timedelta(seconds=60)

# Named-credential lists change very rarely; poll them infrequently.
CRED_UPDATE_INTERVAL = timedelta(minutes=5)

# addrType -> credential category (POST /api_v2/addrNickname).
CREDENTIAL_TYPES: dict[str, int] = {
    "passwords": 0,
    "visitor_passwords": 6,
    "cards": 3,
    "fingerprints": 5,
    "faces": 7,
}
