import hashlib
import hmac
import json
import time

from urllib.parse import parse_qsl, unquote


class TelegramAuthError(Exception):
    pass


def validate_init_data(
    init_data: str,
    bot_token: str,
    max_age: int = 86400,  # 24 hours
) -> dict:
    """
    Checks initData Telegram Mini App.

    returns user data:
    {
        "id": 123,
        "first_name": "Alex",
        ...
    }
    """

    try:
        parsed = dict(
            (key, unquote(value))
            for key, value in parse_qsl(init_data)
        )

    except Exception:
        raise TelegramAuthError("Invalid init data format")


    received_hash = parsed.pop("hash", None)

    if not received_hash:
        raise TelegramAuthError("Hash missing")


    auth_date = int(parsed.get("auth_date", 0))

    if time.time() - auth_date > max_age:
        raise TelegramAuthError("Init data expired")


    # The string that telegram requires
    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(parsed.items())
    )


    # secret_key = HMAC_SHA256("WebAppData", bot_token)

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()


    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()


    if not hmac.compare_digest(
        calculated_hash,
        received_hash
    ):
        raise TelegramAuthError(
            "Invalid Telegram signature"
        )


    if "user" not in parsed:
        raise TelegramAuthError(
            "User data missing"
        )


    return json.loads(parsed["user"])