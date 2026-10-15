"""API client for the Solity / 3elock cloud service.

Login model verified against the production server: the 6-digit app password
is used as emailId + phoneToken, and hashedPwd = base64(sha256(password)),
with appSource="0" and lang="3". Success is contents.loginResult == 0.
"""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import hashlib
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientError, ClientSession

BASE_URL = "https://www.smartsolity.com/api_v2"
REQUEST_TIMEOUT = 10


class SmartSolityError(Exception):
    """Base error for the 3elock API client."""


class SmartSolityAuthError(SmartSolityError):
    """Raised when login, or a relogin attempt, fails."""


class SmartSolityApiError(SmartSolityError):
    """Raised when an authenticated call keeps failing after a successful relogin."""


class SmartSolityConnectionError(SmartSolityError):
    """Raised when the API cannot be reached."""


@dataclass
class SmartSolityDevice:
    """Static metadata for a Solity lock device."""

    device_id: str
    nickname: str
    maker_name: str
    model_name: str


class SmartSolityApiClient:
    """Client for the smartsolity.com cloud API."""

    def __init__(self, session: ClientSession, password: str) -> None:
        """Initialize the client. `password` is the 6-digit app password."""
        self._session = session
        self._password = password
        self._token: str | None = None

    async def login(self) -> None:
        """Log in and store the session token."""
        hashed_pwd = base64.b64encode(
            hashlib.sha256(self._password.encode()).digest()
        ).decode()
        payload = {
            "phoneToken": self._password,
            "hashedPwd": hashed_pwd,
            "appSource": "0",
            "emailId": self._password,
            "lang": "3",
        }
        data = await self._request("POST", "/login", payload)
        contents = data.get("contents") or {}
        if data.get("result") != 0 or contents.get("loginResult") != 0:
            raise SmartSolityAuthError(
                contents.get("loginMessage") or "invalid credentials"
            )
        self._token = contents["token"]

    async def get_my_device(self) -> SmartSolityDevice:
        """Return the single lock device registered to this account."""
        data = await self._authorized_request("GET", "/myDevice")
        device = data["contents"]["myDeviceList"][0]
        return SmartSolityDevice(
            device_id=device["myDeviceId"],
            nickname=device["myDeviceNickName"],
            maker_name=device["myDeviceMakerName"],
            model_name=device["myDeviceModelName"],
        )

    async def get_device_status(self) -> dict[str, Any] | None:
        """Poll /myDevice and return the full device record (raw fields).

        The API responds with HTTP 304 when nothing has changed since the
        last poll, in which case None is returned.
        """
        if self._token is None:
            await self.login()
        data = await self._get_my_device_conditional()
        if data is None:
            return None
        if data.get("result") != 0:
            await self.login()
            data = await self._get_my_device_conditional()
            if data is None:
                return None
            if data.get("result") != 0:
                raise SmartSolityApiError(data.get("errorMessage") or "request failed")
        return data["contents"]["myDeviceList"][0]

    async def get_logs(
        self, device_id: str, length: int = 20, timezone: str = "+0:00"
    ) -> list[dict[str, Any]]:
        """Return the most recent access-log entries (newest first)."""
        query = urlencode(
            {
                "pMemberId": "",
                "pLogType": "",
                "pLogStart": 0,
                "pLogLength": length,
                "pTimezone": timezone,
            }
        )
        data = await self._authorized_request(
            "GET", f"/retrieveLog/page/{device_id}?{query}"
        )
        contents = data.get("contents") or {}
        return contents.get("retrieveLogList") or []

    async def lock(self, device_id: str) -> None:
        """Lock the device (lockerStatus goes to '0')."""
        await self._authorized_request(
            "PUT",
            f"/controlDevice/{device_id}",
            {"lang": "3", "appSource": "0", "optionValue": "1", "controlType": "close"},
        )

    async def unlock(self, device_id: str) -> None:
        """Unlock the device."""
        await self._authorized_request(
            "PUT",
            f"/controlDevice/{device_id}",
            {"lang": "3", "appSource": "0", "optionValue": "1", "controlType": "open"},
        )

    async def _authorized_request(
        self, method: str, path: str, payload: dict[str, str] | None = None
    ) -> dict:
        """Make an authenticated request, retrying once after a fresh login."""
        if self._token is None:
            await self.login()
        data = await self._request(method, path, payload)
        if data.get("result") != 0:
            await self.login()
            data = await self._request(method, path, payload)
            if data.get("result") != 0:
                raise SmartSolityApiError(data.get("errorMessage") or "request failed")
        return data

    async def _request(
        self, method: str, path: str, payload: dict[str, str] | None = None
    ) -> dict:
        """Make a single request to the API."""
        headers = {"Authorization": self._token} if self._token else {}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.request(
                    method, f"{BASE_URL}{path}", json=payload, headers=headers
                )
                return await response.json(content_type=None)
        except (TimeoutError, ClientError) as err:
            raise SmartSolityConnectionError(str(err)) from err

    async def _get_my_device_conditional(self) -> dict | None:
        """GET /myDevice, returning None when the server responds 304 Not Modified."""
        headers = {"Authorization": self._token} if self._token else {}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.request(
                    "GET", f"{BASE_URL}/myDevice", headers=headers
                )
                if response.status == 304:
                    return None
                return await response.json(content_type=None)
        except (TimeoutError, ClientError) as err:
            raise SmartSolityConnectionError(str(err)) from err
