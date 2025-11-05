from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подборка", callback_data="selection")],
            [InlineKeyboardButton(text="Мои оценки", callback_data="my_ratings")],
            [InlineKeyboardButton(text="Подборка по описанию", callback_data="by_description")],
            [InlineKeyboardButton(text="Поиск", callback_data="search_books")]
        ]
    )
