from fastapi import Header, HTTPException

from dotenv import load_dotenv
import os

from api.auth_utils import (
    validate_init_data,
    TelegramAuthError
)


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')


async def get_current_telegram_user(
    authorization: str = Header(...)
):

    if not authorization.startswith("tma "):
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
        return {
            'id': 2, 
            'first_name': 'Кто-то', 
            'last_name': '', 
            'username': '@somebody', 
            'language_code': 'en', 
            'is_premium': True, 
            'allows_write_to_pm': True, 
            'photo_url': 'https://t.me/i/userpic/320/krqI_gAd5zUEZ2MBqMS8J9-RvWFfV6Y19qIo0EG1e_E.svg'
        }

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

    return user


# async def get_current_telegram_user():
#     return {'id': 801762750, 'first_name': 'Валера', 'last_name': '', 'username': 'valerawd', 'language_code': 'en', 'is_premium': True, 'allows_write_to_pm': True, 'photo_url': 'https://t.me/i/userpic/320/krqI_gAd5zUEZ2MBqMS8J9-RvWFfV6Y19qIo0EG1e_E.svg'}
