from fastapi import Header, HTTPException, Request, WebSocket

from dotenv import load_dotenv
import os

from api.auth_utils import (
    validate_init_data,
    TelegramAuthError
)


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DEV_AUTH_TOKEN  = os.getenv('DEV_AUTH_TOKEN')
DEV_IP  = os.getenv('DEV_IP')
DEV_USER = {
    "id": 2,
    "first_name": "Test",
    "last_name": "User",
    "username": "test_user",
    "language_code": "en",
    "is_premium": True,
    "allows_write_to_pm": True,
    "photo_url": None
}


async def get_current_telegram_user(
    authorization: str = Header(...),
    request: Request = None,
    websocket: WebSocket = None,
):
    print('get_current_telegram_user()')
    
    if not authorization.startswith("tma "):
        print(1)
        raise HTTPException(
            status_code=401,
            detail="Invalid auth header"
        )


    init_data = authorization[4:]


    try:
        user = validate_init_data(
            init_data,
            BOT_TOKEN
        )

    except TelegramAuthError as e:
        # dev bypass
        if (request and request.headers.get("X-Dev-Auth") == DEV_AUTH_TOKEN 
                or websocket and websocket.headers.get("x-real-ip") == DEV_IP):
            return DEV_USER
        print(2)
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

    return user


# async def get_current_telegram_user():
#     return {'id': 801762750, 'first_name': 'Валера', 'last_name': '', 'username': 'valerawd', 'language_code': 'en', 'is_premium': True, 'allows_write_to_pm': True, 'photo_url': 'https://t.me/i/userpic/320/krqI_gAd5zUEZ2MBqMS8J9-RvWFfV6Y19qIo0EG1e_E.svg'}
