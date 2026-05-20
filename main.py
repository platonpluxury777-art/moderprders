import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from config import BOT_TOKEN
from database_json import init_db
from handlers import router

async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(router)
    
    commands = [
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="balance", description="Баланс"),
        BotCommand(command="daily", description="Ежедневная награда"),
        BotCommand(command="top", description="Топ пользователей"),
        BotCommand(command="staff", description="Персонал"),
        BotCommand(command="rules", description="Правила"),
    ]
    await bot.set_my_commands(commands)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())