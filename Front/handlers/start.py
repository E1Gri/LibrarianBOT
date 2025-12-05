from aiogram import types, Router
from aiogram.filters import Command
from Front.keyboards.main_menu import main_menu


router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = ("""
    📚 Добро пожаловать! Я ваш персональный библиотекарь! 📚

Ищете новую любимую книгу, подборку под настроение или конкретное произведение? Просто скажите и я найду то, что зацепит с первой страницы — всего за пару кликов! 

✨ Что я умею:
🔹 Подборка по описанию — опишите, что хотите прочитать (жанр, настроение, сюжет), и я подберу книги, идеально соответствующие вашему запросу.
🔹 Поиск по названию — введите название книги — и я найду её мгновенно.
🔹 Мои оценки & Подборки — просмотрите все свои лайки, дизлайки и созданные подборки. Всё под рукой!

❤️ Просто нажмите кнопку — и начнём путешествие!
""")
    await message.answer(welcome_text, reply_markup=main_menu())
