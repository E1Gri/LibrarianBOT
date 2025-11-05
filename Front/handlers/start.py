from aiogram import types, Router
from aiogram.filters import Command
from keyboards.main_menu import main_menu


router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = "Привет, я бот библиотекарь\n❤️❤️❤️"
    await message.answer(welcome_text, reply_markup=main_menu())
