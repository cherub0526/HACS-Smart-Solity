"""Constants for the Smart Solity (cloud) integration.

All values here were recovered by static analysis of the Smart Solity
Android app (kr.co.h_gang.smartsolity 2.0.17). They are the app's own
API contract and are treated as data, not verified runtime behavior.
Anything marked UNVERIFIED still needs a real server round-trip to confirm.
"""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "smart_solity"

# Production backend (assets/config.json -> API_URL). ":443" implied by https.
BASE_URL = "https://www.smartsolity.com"

# Retrofit timeouts from config.json (connect 25s / read 65s).
CONNECT_TIMEOUT = 25
READ_TIMEOUT = 65

# How often to poll the cloud for device state.
SCAN_INTERVAL = timedelta(seconds=30)

# --- API paths (net/service/*Service.java) ---
PATH_LOGIN = "/api_v2/login"
PATH_LOGIN_REISSUE = "/api_v2/login/reissue"
PATH_MY_DEVICE = "/api_v2/myDevice"
PATH_CONTROL_DEVICE = "/api_v2/controlDevice/{my_device_id}"

# --- Headers (net/interceptor/TokenInterceptor.java) ---
HEADER_AUTH = "Authorization"
HEADER_AUTH_PWD = "AuthorizationPwd"

# Res envelope success code (data/Res.java: result == 0 means success).
RESULT_OK = 0

# Login body fields (repository/LoginRepository.login).
# NOTE: appSource is set at runtime in the app (MainApplication, default "").
# Left empty by default; override via integration options if the server rejects it.
DEFAULT_APP_SOURCE = ""
DEFAULT_LANG = "ko"

# --- controlDevice control types (base/Constants.java -> Api) ---
CONTROL_OPEN = "open"            # remote unlock; optionValue "1"
CONTROL_CLOSE = "close"          # lock / deadbolt
CONTROL_GET_STATUS = "get_status"
CONTROL_GET_FUNCTION = "get_function"
OPTION_DEFAULT = "1"

# lockerStatus interpretation (UNVERIFIED mapping; refined from EVENT_CODE_*:
# close="0", deadbolt="1"). Treat these tokens as "locked".
LOCKED_TOKENS = {"1", "close", "closed", "lock", "locked", "deadbolt"}
UNLOCKED_TOKENS = {"0", "open", "opened", "unlock", "unlocked", "release"}

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_APP_SOURCE = "app_source"
