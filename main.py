from aiogram import Bot, Dispatcher
import asyncio
import logging

from handlers import commands, admin, operator, student
from settings import TOKEN
from data.models import async_main


logging.basicConfig(
    format=f'%(asctime)s - %(name)s - %(levelname)s - %(message)s',filemode='w',
    level=logging.ERROR, filename='bot.log')

async def main():
    await async_main()
    
    bot = Bot(token=TOKEN)
    bot.default.parse_mode = 'HTML'
    dp = Dispatcher()
    dp.include_routers(
        commands.router,
        operator.router,
        admin.router,
        student.router,
        )
    
    await dp.start_polling(bot, drop_pending_updates=True)
            

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Работа бота завершена')
