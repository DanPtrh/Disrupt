import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import load_settings
from bot.logging_config import setup_logging
from bot.middlewares.role_middleware import RoleMiddleware

from bot.routers.start import router as start_router
from bot.routers.game import router as game_router
from bot.routers.solutions import router as solutions_router
from bot.routers.admin import router as admin_router
from bot.routers.profile import router as profile_router


async def main():
    setup_logging()
    settings = load_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.message.middleware(RoleMiddleware(settings=settings))
    dp.callback_query.middleware(RoleMiddleware(settings=settings))

    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(game_router)
    dp.include_router(solutions_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
