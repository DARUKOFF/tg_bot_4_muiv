from aiogram.filters import Filter
from aiogram.types import Message

from settings import ADMIN_USER_IDS


class IsAdmin(Filter):
    async def __call__(self, message: Message):
        return message.from_user.id in ADMIN_USER_IDS
    