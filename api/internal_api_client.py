import aiohttp


MESSENGER_API_URL = "https://wdraft.online/api"
BOT_API_URL = "http://localhost:8081/api"

class InternalApiClient:
    def __init__(self, internal_api_key):
        self.internal_api_key = internal_api_key
        self._session = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        await self.session.close()
    
    async def send_system_message(
        self,
        order_id: int,
        text: str,
    ):
        """
        Send system message to messanger's chat
        """
        print('send_system_message()')
        
        return await self._post(
            MESSENGER_API_URL,
            f"/internal/chat/{order_id}/message",
            {"text": text},
        )

    async def send_bot_notification(
        self,
        tg_chat_id: int,
        text: str,
        order_id: int
    ):
        """
        Send notification to user through his tg chat with bot
        """
        print('send_bot_notification()')
        
        return await self._post(
            BOT_API_URL,
            f"/internal/bot_chat/{tg_chat_id}/message",
            {"text": text, "order_id": order_id},
        )
            
    async def _post(
        self,
        base_url: str,
        path: str,
        body: dict,
    ):
        session = await self.get_session()
        async with session.post(
            f"{base_url}{path}",
            headers={
                "X-Internal-Key": self.internal_api_key,
            },
            json=body,
        ) as response:

            if response.status != 200:
                raise Exception(await response.text())

            return await response.json()