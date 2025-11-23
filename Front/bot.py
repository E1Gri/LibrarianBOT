import asyncio
import logging
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os

# Импорт роутеров
from handlers.start import router as start_router
from handlers.book_handlers import router as book_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    
    # Загрузка токена из .env или config.env
    load_dotenv()
    load_dotenv('config.env')  # На случай если токен в config.env
    
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        logger.error("Токен бота не найден! Создайте файл .env с BOT_TOKEN")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Подключение роутеров
    dp.include_router(start_router)
    dp.include_router(book_router)
    
    logger.info("Бот запущен и готов к работе!")
    
    try:
        # Запуск polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
