"""Async client for the Smart Solity cloud API.

Reverse-engineered from the Smart Solity Android app. The request/response
shapes come from the app's Retrofit services and Gson models:
  - Res<T>      = {result, errorMessage, contentsmyDeviceMessage, contents}
  - LoginBean   = {token, tokenPwd, loginResult, loginMessage, memberInfo}
  - MyDeviceBean= {myDeviceList: [...], myDeviceListCount}
  - ControlResult = {controlDeviceResult, controlDeviceMessage}
"""

from __future__ import annotations

import base64
import hashlib
import logging
from typing import Any

import aiohttp

from .const import (
    BASE_URL,
    DEFAULT_APP_SOURCE,
    DEFAULT_LANG,
    HEADER_AUTH,
    HEADER_AUTH_PWD,
    PATH_CONTROL_DEVICE,
    PATH_LOGIN,
    PATH_MY_DEVICE,
    READ_TIMEOUT,
    RESULT_OK,
)

_LOGGER = logging.getLogger(__name__)


class SmartSolityError(Exception):
    """Generic API error with the server's result code / message."""

    def __init__(self, message: str, result: int | None = None) -> None:
        super().__init__(message)
        self.result = result


class SmartSolityAuthError(SmartSolityError):
    """Authentication failed or the session token is no longer valid."""


def hash_password(password: str) -> str:
    """Reproduce EncryptUtils.encryptSHA256: base64(sha256(utf8(password))).

    The app uses Base64.encodeToString(digest, NO_WRAP), NOT hex.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


class SmartSolityApi:
    """Thin async wrapper over the Smart Solity /api_v2 endpoints."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
        *,
        app_source: str = DEFAULT_APP_SOURCE,
        lang: str = DEFAULT_LANG,
        phone_token: str = "",
    ) -> None:
        self._session = session
        self._email = email
        self._hashed_pwd = hash_password(password)
        self._app_source = app_source
        self._lang = lang
        self._phone_token = phone_token
        self._token: str | None = None
        self._token_pwd: str | None = None

    @property
    def token(self) -> str | None:
        return self._token

    async def login(self) -> dict[str, Any]:
        """POST /api_v2/login. Stores token + tokenPwd on success."""
        body = {
            "emailId": self._email,
            "hashedPwd": self._hashed_pwd,
            "phoneToken": self._phone_token,
            "appSource": self._app_source,
            "lang": self._lang,
        }
        contents = await self._request("POST", PATH_LOGIN, json=body, auth=False)
        self._token = contents.get("token")
        self._token_pwd = contents.get("tokenPwd")
        if not self._token:
            raise SmartSolityAuthError("Login succeeded but no token was returned")
        return contents

    async def get_devices(self) -> list[dict[str, Any]]:
        """GET /api_v2/myDevice -> list of MyDeviceList dicts."""
        contents = await self._request("GET", PATH_MY_DEVICE)
        devices = contents.get("myDeviceList") or []
        if not isinstance(devices, list):
            raise SmartSolityError("Unexpected myDeviceList shape")
        return devices

    async def control(
        self, my_device_id: str, control_type: str, option_value: str = "1"
    ) -> dict[str, Any]:
        """PUT /api_v2/controlDevice/{id} with {controlType, optionValue}."""
        path = PATH_CONTROL_DEVICE.format(my_device_id=my_device_id)
        body = {"controlType": control_type, "optionValue": option_value}
        return await self._request("PUT", path, json=body)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        auth: bool = True,
        _retry: bool = True,
    ) -> dict[str, Any]:
        """Perform a request and unwrap the Res<T> envelope -> contents.

        On an auth failure for an authenticated call, re-login once and retry.
        """
        headers = {"Connection": "close"}
        if auth:
            if not self._token:
                await self.login()
            headers[HEADER_AUTH] = self._token or ""
            if self._token_pwd:
                headers[HEADER_AUTH_PWD] = self._token_pwd

        url = f"{BASE_URL}{path}"
        timeout = aiohttp.ClientTimeout(total=READ_TIMEOUT)
        try:
            async with self._session.request(
                method, url, json=json, params=params, headers=headers, timeout=timeout
            ) as resp:
                text = await resp.text()
                if resp.status in (401, 403):
                    if auth and _retry:
                        await self.login()
                        return await self._request(
                            method, path, json=json, params=params, auth=auth, _retry=False
                        )
                    raise SmartSolityAuthError(f"HTTP {resp.status}: {text[:200]}")
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise SmartSolityError(f"Network error calling {path}: {err}") from err

        if not isinstance(data, dict):
            raise SmartSolityError(f"Unexpected response from {path}: {data!r}")

        result = data.get("result")
        contents = data.get("contents")
        if result is not None and result != RESULT_OK:
            message = data.get("errorMessage") or data.get("contentsmyDeviceMessage") or ""
            # A non-zero result on an authenticated call often means a stale token.
            if auth and _retry and result in (401, 403):
                await self.login()
                return await self._request(
                    method, path, json=json, params=params, auth=auth, _retry=False
                )
            raise SmartSolityError(f"API result={result} for {path}: {message}", result)

        # contents may be the payload object, or absent for simple acks.
        if isinstance(contents, dict):
            return contents
        return data
