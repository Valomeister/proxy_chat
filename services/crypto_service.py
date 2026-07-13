import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv


load_dotenv()

print(os.getenv("MESSAGE_ENCRYPTION_KEY"))

class CryptoService:

    _fernet = Fernet(
        os.getenv("MESSAGE_ENCRYPTION_KEY").encode()
    )


    @classmethod
    def encrypt(cls, text: str) -> str:
        return cls._fernet.encrypt(
            text.encode()
        ).decode()


    @classmethod
    def decrypt(cls, encrypted: str) -> str:
        return cls._fernet.decrypt(
            encrypted.encode()
        ).decode()