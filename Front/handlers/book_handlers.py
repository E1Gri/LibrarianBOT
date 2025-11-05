from aiogram import types, Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.input_file import FSInputFile
from test_books import books
from keyboards.main_menu import main_menu


router = Router()


# --- ХРАНЕНИЕ СОСТОЯНИЙ ПОЛЬЗОВАТЕЛЕЙ ---
user_feedback = {}  # {user_id: {"likes": [], "dislikes": [], "bookmarks": [], "index": 0, "current_category": None, "history": [], "search_results": [], "source": None, "current_index_in_list": None}}


# --- КЛАВИАТУРЫ ---
def book_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 Лайк", callback_data="like"),
            InlineKeyboardButton(text="👎 Дизлайк", callback_data="dislike"),
            InlineKeyboardButton(text="🔖 В закладки", callback_data="bookmark")
        ],
        [
            InlineKeyboardButton(text="⬅️ Предыдущая", callback_data="prev"),
            InlineKeyboardButton(text="➡️ Следующая", callback_data="next")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")
        ]
    ])


def book_keyboard_in_list() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 Лайк", callback_data="like_no_next"),
            InlineKeyboardButton(text="👎 Дизлайк", callback_data="dislike_no_next"),
            InlineKeyboardButton(text="🔖 В закладки", callback_data="bookmark_no_next")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_from_book")
        ]
    ])


def ratings_menu_all() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Лайки", callback_data="show_likes"),
            InlineKeyboardButton(text="💔 Дизлайки", callback_data="show_dislikes"),
            InlineKeyboardButton(text="🔖 Закладки", callback_data="show_bookmarks")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
        ]
    ])


def ratings_menu_category() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_all_ratings")
        ]
    ])


def search_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main_from_search")
        ]
    ])


# --- ПОДБОРКА ---
async def send_book(message: types.Message, user_id: int, edit=False):
    index = user_feedback[user_id]["index"]
    book = books[index]
    photo = FSInputFile(book["cover"])
    caption = f"<b>{book['title']}</b>\nАвтор: {book['author']}\n\n{book['description']}"
    if edit:
        await message.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"),
            reply_markup=book_keyboard()
        )
    else:
        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=book_keyboard())


@router.callback_query(lambda c: c.data == "selection")
async def selection_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_feedback.setdefault(user_id, {"likes": [], "dislikes": [], "bookmarks": [],
                                       "index": 0, "current_category": None, "history": [],
                                       "search_results": [], "source": None, "current_index_in_list": None})
    await send_book(callback_query.message, user_id)
    await callback_query.answer()


# --- ОБЩАЯ ОЦЕНКА ---
async def give_feedback(data, book, feedback_type):
    # Ограничение: лайк и дизлайк одновременно нельзя
    if feedback_type == "like":
        if book in data["dislikes"]:
            data["dislikes"].remove(book)
        if book not in data["likes"]:
            data["likes"].append(book)
    elif feedback_type == "dislike":
        if book in data["likes"]:
            data["likes"].remove(book)
        if book not in data["dislikes"]:
            data["dislikes"].append(book)
    elif feedback_type == "bookmark":
        if book not in data["bookmarks"]:
            data["bookmarks"].append(book)


@router.callback_query(lambda c: c.data in ["like", "dislike", "bookmark"])
async def feedback_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    index = user_feedback[user_id]["index"]
    book = books[index]
    data = user_feedback[user_id]

    if callback_query.data == "like":
        await give_feedback(data, book, "like")
        msg = "❤️ Лайк"
    elif callback_query.data == "dislike":
        await give_feedback(data, book, "dislike")
        msg = "💔 Дизлайк"
    else:
        await give_feedback(data, book, "bookmark")
        msg = "🔖 В закладки"

    await callback_query.answer(msg, show_alert=False)

    # Следующая книга в подборке
    data["index"] = (data["index"] + 1) % len(books)
    await send_book(callback_query.message, user_id, edit=True)


# --- Навигация подборки ---
@router.callback_query(lambda c: c.data in ["next", "prev"])
async def nav_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if callback_query.data == "next":
        user_feedback[user_id]["index"] = (user_feedback[user_id]["index"] + 1) % len(books)
    else:
        user_feedback[user_id]["index"] = (user_feedback[user_id]["index"] - 1) % len(books)
    await send_book(callback_query.message, user_id, edit=True)
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "menu")
async def back_to_menu(callback_query: types.CallbackQuery):
    await callback_query.message.answer("🏠 Главное меню", reply_markup=main_menu())
    await callback_query.answer()


# --- МОИ ОЦЕНКИ ---
@router.callback_query(lambda c: c.data == "my_ratings")
async def my_ratings_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_feedback.setdefault(user_id, {"likes": [], "dislikes": [], "bookmarks": [],
                                       "index": 0, "current_category": None, "history": [],
                                       "search_results": [], "source": None, "current_index_in_list": None})
    user_feedback[user_id]["history"] = []
    data = user_feedback[user_id]

    likes = data["likes"]
    dislikes = data["dislikes"]
    bookmarks = data["bookmarks"]

    all_rated = []
    for b in likes:
        all_rated.append(f"❤️ {b['title']}")
    for b in dislikes:
        all_rated.append(f"💔 {b['title']}")
    for b in bookmarks:
        all_rated.append(f"🔖 {b['title']}")

    if not all_rated:
        text = "😶 Вы ещё не оценили ни одной книги."
    else:
        text = "📚 <b>Все ваши оценки:</b>\n\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(all_rated))

    data["history"].append("all_ratings")
    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=ratings_menu_all())
    await callback_query.answer()


@router.callback_query(lambda c: c.data in ["show_likes", "show_dislikes", "show_bookmarks"])
async def show_category_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_feedback[user_id]
    data["current_category"] = callback_query.data.split("_")[1]
    data["history"].append("category_menu")
    data["source"] = "ratings"

    category_name = {"likes": "❤️ Лайки", "dislikes": "💔 Дизлайки", "bookmarks": "🔖 Закладки"}[data["current_category"]]
    books_list = data[data["current_category"]]

    if not books_list:
        text = f"{category_name}:\n\nПока нет книг."
    else:
        text = f"{category_name}:\n\n" + "\n".join(f"{i+1}. {b['title']}" for i, b in enumerate(books_list))
        text += "\n\n📖 Введите номер книги, чтобы увидеть карточку."

    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=ratings_menu_category())
    await callback_query.answer()


# --- ПОИСК ---
@router.callback_query(lambda c: c.data == "search_books")
async def start_search_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_feedback.setdefault(user_id, {"likes": [], "dislikes": [], "bookmarks": [],
                                       "index": 0, "current_category": None, "history": [],
                                       "search_results": [], "source": None, "current_index_in_list": None})
    user_feedback[user_id]["source"] = "search"
    user_feedback[user_id]["search_results"] = []
    user_feedback[user_id]["current_index_in_list"] = None
    
    await callback_query.message.answer("🔍 Введите часть названия книги для поиска:", reply_markup=search_menu())
    await callback_query.answer()


# --- ОБРАБОТЧИК ТЕКСТА ---
@router.message(lambda message: True)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    data = user_feedback.setdefault(user_id, {"likes": [], "dislikes": [], "bookmarks": [],
                                              "index": 0, "current_category": None, "history": [],
                                              "search_results": [], "source": None, "current_index_in_list": None})

    text = message.text.strip()

    # --- ОБРАБОТКА ВВОДА ЦИФР ДЛЯ ОТКРЫТИЯ КНИГИ ---
    # Цифры = номер книги ТОЛЬКО если уже есть результаты поиска или список оценок
    if text.isdigit() and data.get("current_index_in_list") is None:
        # Проверяем, есть ли список книг для выбора
        has_results = False
        books_list = []
        
        if data.get("source") == "search" and data.get("search_results"):
            books_list = data["search_results"]
            has_results = True
        elif data.get("source") == "ratings" and data.get("current_category"):
            books_list = data[data["current_category"]]
            has_results = True
        
        # Если есть список - обрабатываем как номер
        if has_results:
            idx = int(text) - 1
            if 0 <= idx < len(books_list):
                book = books_list[idx]
                data["current_index_in_list"] = idx
                photo = FSInputFile(book["cover"])
                caption = f"<b>{book['title']}</b>\nАвтор: {book['author']}\n\n{book['description']}"
                await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML", reply_markup=book_keyboard_in_list())
                return
            else:
                await message.answer("❌ Неверный номер книги.")
                return
        # Если списка нет - продолжаем обработку как поискового запроса

    # --- ПОИСК ---
    if data.get("source") == "search":
        # Общий поиск по всем книгам (включая "1984")
        query = text.lower()
        results = [b for b in books if query in b["title"].lower()]
        data["search_results"] = results
        if not results:
            await message.answer("❌ Ничего не найдено.", reply_markup=search_menu())
            return
        text_out = "🔍 Найдено:\n\n" + "\n".join(f"{i+1}. {b['title']}" for i, b in enumerate(results))
        text_out += "\n\nВведите номер книги, чтобы открыть её."
        await message.answer(text_out, reply_markup=search_menu())
    
    elif data.get("source") == "ratings" and data.get("current_category"):
        # Поиск внутри категории оценок
        query = text.lower()
        category = data["current_category"]
        all_books = data[category]
        results = [b for b in all_books if query in b["title"].lower()]
        
        category_name = {"likes": "❤️ Лайки", "dislikes": "💔 Дизлайки", "bookmarks": "🔖 Закладки"}[category]
        
        if not results:
            await message.answer(f"❌ Ничего не найдено в категории {category_name}.", reply_markup=ratings_menu_category())
            return
        
        text_out = f"🔍 Найдено в {category_name}:\n\n" + "\n".join(f"{i+1}. {b['title']}" for i, b in enumerate(results))
        text_out += "\n\nВведите номер книги, чтобы открыть её."
        
        await message.answer(text_out, reply_markup=ratings_menu_category())


# --- ОБРАБОТЧИКИ КНОПОК НАЗАД ---
@router.callback_query(lambda c: c.data == "back_from_book")
async def back_from_book_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_feedback[user_id]
    
    data["current_index_in_list"] = None
    
    source = data.get("source")
    if source == "search":
        results = data["search_results"]
        if not results:
            await callback_query.message.answer("❌ Ничего не найдено.", reply_markup=search_menu())
            await callback_query.answer()
            return
        text = "🔍 Найдено:\n\n" + "\n".join(f"{i+1}. {b['title']}" for i, b in enumerate(results))
        text += "\n\nВведите номер книги, чтобы открыть её."
        await callback_query.message.answer(text, reply_markup=search_menu())
    elif source == "ratings":
        category = data.get("current_category")
        books_list = data.get(category, [])
        category_name = {"likes": "❤️ Лайки", "dislikes": "💔 Дизлайки", "bookmarks": "🔖 Закладки"}[category]
        if not books_list:
            text = f"{category_name}:\n\nПока нет книг."
        else:
            text = f"{category_name}:\n\n" + "\n".join(f"{i+1}. {b['title']}" for i, b in enumerate(books_list))
            text += "\n\n📖 Введите номер книги, чтобы увидеть карточку."
        await callback_query.message.answer(text, reply_markup=ratings_menu_category())
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "back_to_all_ratings")
async def back_to_all_ratings_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_feedback[user_id]
    
    data["source"] = None
    data["current_category"] = None
    data["current_index_in_list"] = None
    
    likes = data["likes"]
    dislikes = data["dislikes"]
    bookmarks = data["bookmarks"]
    all_rated = []
    for b in likes:
        all_rated.append(f"❤️ {b['title']}")
    for b in dislikes:
        all_rated.append(f"💔 {b['title']}")
    for b in bookmarks:
        all_rated.append(f"🔖 {b['title']}")
    if not all_rated:
        text = "😶 Вы ещё не оценили ни одной книги."
    else:
        text = "📚 <b>Все ваши оценки:</b>\n\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(all_rated))
    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=ratings_menu_all())
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_feedback.get(user_id)
    
    if data:
        data["source"] = None
        data["current_category"] = None
        data["current_index_in_list"] = None
        data["search_results"] = []
    
    await callback_query.message.answer("🏠 Главное меню", reply_markup=main_menu())
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "back_to_main_from_search")
async def back_to_main_from_search_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_feedback.get(user_id)
    
    if data:
        data["source"] = None
        data["search_results"] = []
        data["current_index_in_list"] = None
    
    await callback_query.message.answer("🏠 Главное меню", reply_markup=main_menu())
    await callback_query.answer()


# --- ОЦЕНКА КНИГ В СПИСКЕ (МОИ ОЦЕНКИ, ПОИСК) ---
@router.callback_query(lambda c: c.data in ["like_no_next", "dislike_no_next", "bookmark_no_next"])
async def feedback_in_list_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_feedback[user_id]
    source = data.get("source")
    if source == "search":
        books_list = data["search_results"]
        idx = data["current_index_in_list"]
    elif source == "ratings":
        category = data["current_category"]
        books_list = data[category]
        idx = data["current_index_in_list"]
    else:
        await callback_query.answer("⚠️ Ошибка источника.", show_alert=True)
        return

    book = books_list[idx]

    if callback_query.data == "like_no_next":
        await give_feedback(data, book, "like")
        msg = "❤️ Лайк"
    elif callback_query.data == "dislike_no_next":
        await give_feedback(data, book, "dislike")
        msg = "💔 Дизлайк"
    else:
        await give_feedback(data, book, "bookmark")
        msg = "🔖 В закладки"

    await callback_query.answer(msg, show_alert=False)
