# Smart Solity — Home Assistant custom integration (cloud)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Unofficial Home Assistant integration for Solity **Smart Solity** door locks,
talking to the official cloud API (`https://www.smartsolity.com`, `/api_v2/*`).
It is the **WiFi / cloud** path: the phone app never speaks Bluetooth or AWS IoT
directly — it calls the REST API and the backend relays to the lock over its own
AWS IoT connection. This integration does the same.

`iot_class: cloud_polling` — state is polled every 30 s; control is a REST call.

## Install via HACS (recommended)

This repo is not in the HACS default store, so add it as a **custom repository**:

1. HACS → ⋮ (top-right) → **Custom repositories**.
2. Repository: `https://github.com/cherub0526/HACS-Smart-Solity` — Category: **Integration** → **Add**.
3. Find **Smart Solity** in HACS → **Download**.
4. **Restart Home Assistant**.
5. Settings → Devices & Services → **Add Integration** → "Smart Solity".
6. Enter the **6-digit app password** shown in the Solity app (e.g. 042636).

You can also open HACS pre-filled with:
[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cherub0526&repository=HACS-Smart-Solity&category=integration)

## Install manually

1. Copy `custom_components/3elock/` into your HA `config/custom_components/`.
2. Restart Home Assistant.
3. Settings → Devices & Services → **Add Integration** → "Smart Solity".
4. Enter the **6-digit app password** shown in the Solity app (e.g. 042636).

## Entities

- **Lock** per registered device — `lock` / `unlock` / `open`.
- **Sensors** — battery (%), firmware version, gateway connection (diagnostic).

## How it was built

The API contract was recovered by static reverse engineering of the Android app
(`kr.co.h_gang.smartsolity` 2.0.17). Key facts baked into `const.py` / `api.py`:

| Thing | Value |
|---|---|
| Login | `POST /api_v2/login` `{emailId, hashedPwd, phoneToken, appSource, lang}` |
| Password | `hashedPwd = base64(sha256(password))` (NOT hex) |
| Token | response `contents.token` → header `Authorization`; `tokenPwd` → `AuthorizationPwd` |
| Devices | `GET /api_v2/myDevice` → `contents.myDeviceList[]` |
| Control | `PUT /api_v2/controlDevice/{myDeviceId}` `{controlType, optionValue}` |
| Unlock | `controlType="open"`, `optionValue="1"` |
| Lock | `controlType="close"` |
| Success | envelope `result == 0` |

## ⚠️ Unverified assumptions (confirm against the real server)

This was written from decompiled code **without** a live server round-trip. The
following may need adjustment once you test with a real account:

1. **`appSource`** is empty by default (the app sets it at runtime). If login is
   rejected, set it via the entry options or edit `DEFAULT_APP_SOURCE`.
2. **`lockerStatus` → locked/unlocked mapping** in `const.py` is a best guess
   (`LOCKED_TOKENS` / `UNLOCKED_TOKENS`). Check the real value and adjust.
3. **Remote `open` (unlock)** exists in the API but may be blocked by the lock's
   firmware or dual-authentication settings — the command may be silently refused.
4. The **Res envelope** error codes for "token expired" are assumed to be 401/403.

## Safety

This controls a physical door lock. Test with `get_status` / lock first; verify
behavior before relying on remote unlock. Use only with locks you own.
