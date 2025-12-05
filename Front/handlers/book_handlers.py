from aiogram import types, Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.input_file import FSInputFile
from Front.test_books import books
from Front.keyboards.main_menu import main_menu
from Back.ml_object import ml
from Data.book_for_tgBot import Book
from Back.ml import get_list_reviews, add_user_to_db
import asyncio

MAX_SHORT = 500
MAX_FULL = 700


router = Router()


# --- ХРАНЕНИЕ СОСТОЯНИЙ ПОЛЬЗОВАТЕЛЕЙ ---
user_feedback = {}  # {user_id: {"likes": [], "dislikes": [], "bookmarks": [], "index": 0, "current_category": None, "history": [], "search_results": [], "source": None, "current_index_in_list": None}}
def init_user(user_id):

    add_user_to_db(user_id)

    user_feedback[user_id] = {
        "likes": [],
        "dislikes": [],
        "bookmarks": [],
        "index": 0,
        "current_category": None,
        "history": [],
        "search_results": [],
        "source": None,
        "current_index_in_list": None,
        "is_full": False,
        "recommendations": [],#ml.recommendations(user_id)
        "text": " "
    }

# --- КЛАВИАТУРЫ ---
def book_keyboard(is_full: bool = False) -> InlineKeyboardMarkup:
    text = "Свернуть" if is_full else "Развернуть полностью"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"📄 {text}", callback_data="toggle_desc"),
        ],
        [
            InlineKeyboardButton(text="👍 Лайк", callback_data="like"),
            InlineKeyboardButton(text="👎 Дизлайк", callback_data="dislike"),
            InlineKeyboardButton(text="🔖 В закладки", callback_data="bookmark"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Предыдущая", callback_data="prev"),
            InlineKeyboardButton(text="➡️ Следующая", callback_data="next"),
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu"),
        ],
    ])





def book_keyboard_in_list(is_full: bool = False) -> InlineKeyboardMarkup:
    text = "Свернуть" if is_full else "Развернуть полностью"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"📄 {text}", callback_data="toggle_desc"),
        ],
        [
            InlineKeyboardButton(text="👍 Лайк", callback_data="like_no_next"),
            InlineKeyboardButton(text="👎 Дизлайк", callback_data="dislike_no_next"),
            InlineKeyboardButton(text="🔖 В закладки", callback_data="bookmark_no_next"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_from_book"),
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu"),
        ],
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
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")
        ]
    ])




def ratings_menu_category() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_all_ratings")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")
        ]
    ])


def search_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main_from_search")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu")
        ]
    ])


# --- ОБРАБОТКА ВВОДА LLM --- 
async def llm_send_book(message: types.Message, user_id: int):
    """
    Этап 1: пользователь вводит описание книги.
    LLM генерирует уточняющий вопрос.
    """
    text = message.text.strip()
    user_feedback[user_id]["text"] = text  # сохраняем исходное описание
    user_feedback[user_id]["source"] = "llm_reply"
    
    # Генерация уточняющего вопроса через LLM
    question = await asyncio.to_thread(ml.llm.questions, text)
    await message.answer(question)


async def llm_reply(message: types.Message, user_id: int, edit=False):
    """
    Этап 2: пользователь отвечает на уточняющий вопрос.
    Объединяем с исходным описанием и ищем книги через ML.
    """
    user_text = message.text.strip()
    base_text = user_feedback[user_id]["text"]
    full_text = base_text + " " + user_text

    # Поиск по описанию через ML
    books = await asyncio.to_thread(ml.DescCossim, full_text)
    if not books:
        await message.answer("❌ По вашему описанию ничего не найдено.")
        return

    user_feedback[user_id]["recommendations"] = books
    user_feedback[user_id]["index"] = 0  # начинаем с первой книги

    # Отправляем первую книгу пользователю
    book_id = books[0]
    book = Book.byID(book_id)
    photo = book.pic
    caption = f"<b>{book.name}</b>\nАвтор: {book.author}\n\n{book.discription[:500]}"

    if edit:
        await message.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"),
            reply_markup=book_keyboard()
        )
    else:
        await message.answer_photo(
            photo=photo, caption=caption, parse_mode="HTML", reply_markup=book_keyboard()
        )

# --- CALLBACK HANDLER ДЛЯ ПОИСКА ПО ОПИСАНИЮ ---
@router.callback_query(lambda c: c.data == "by_description")
async def by_description_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_feedback:
        init_user(user_id)

    user_feedback[user_id]["source"] = "description_search"
    user_feedback[user_id]["index"] = 0

    await callback_query.message.answer(
        "🔍 Введите описание книги, чтобы найти её:"
    )
    await callback_query.answer()

# --- ПОДБОРКА ---
async def send_book(message: types.Message, user_id: int, edit=False):
    books = user_feedback[user_id]["recommendations"]
    index = user_feedback[user_id]["index"]
    book_id = books[index]

    book = Book.byID(book_id)
    photo = book.pic

    is_full = user_feedback[user_id].get("is_full", False)
    if is_full:
        desc = (book.discription or "")[:MAX_FULL]
    else:
        desc = (book.discription or "")[:MAX_SHORT]

    caption = f"<b>{desc}</b>\n\n\n{book.name}\nАвтор:{book.author}"

    if edit:
        await message.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"),
            reply_markup=book_keyboard(is_full=is_full),
        )
    else:
        await message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=book_keyboard(is_full=is_full),
        )


@router.callback_query(lambda c: c.data == "selection")
async def selection_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_feedback:
        init_user(user_id)

    data = user_feedback[user_id]
    data["index"] = 0
    data["recommendations"] = ml.recommendations(user_id)
    data["is_full"] = False          # при открытии подборки описание свернуто

    await send_book(callback_query.message, user_id)
    await callback_query.answer()


# --- ОБЩАЯ ОЦЕНКА ---
async def give_feedback(user_id, book: Book, feedback_type):
    # Ограничение: лайк и дизлайк одновременно нельзя
    if feedback_type == "like":
        book.review(user_id, 1)
    elif feedback_type == "dislike":
        book.review(user_id, 2)
    elif feedback_type == "bookmark":
        book.review(user_id, 3)


@router.callback_query(lambda c: c.data in ["like", "dislike", "bookmark"])
async def feedback_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    index = user_feedback[user_id]["index"]
    books = user_feedback[user_id]["recommendations"]
    book = Book.byID(books[index])
    data = user_feedback[user_id]

    if callback_query.data == "like":
        await give_feedback(user_id, book, "like")
        msg = "❤️ Лайк"
    elif callback_query.data == "dislike":
        await give_feedback(user_id, book, "dislike")
        msg = "💔 Дизлайк"
    else:
        await give_feedback(user_id, book, "bookmark")
        msg = "🔖 В закладки"

    await callback_query.answer(msg, show_alert=False)

    # Следующая книга в подборке
    data["index"] = (data["index"] + 1) % len(books)
    await send_book(callback_query.message, user_id, edit=True)


# --- Навигация подборки ---
@router.callback_query(lambda c: c.data in ["next", "prev"])
async def nav_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_feedback:
        init_user(user_id)

    data = user_feedback[user_id]

    if callback_query.data == "next":
        data["index"] = (data["index"] + 1) % len(data["recommendations"])
    else:
        data["index"] = (data["index"] - 1) % len(data["recommendations"])

    data["is_full"] = False  # новая книга -> описание свернуто

    await send_book(callback_query.message, user_id, edit=True)
    await callback_query.answer()



@router.callback_query(lambda c: c.data == "menu")
async def back_to_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = user_feedback.get(user_id)
    if data:
        data["last_menu"] = "main"

    await callback_query.message.answer("🏠 Главное меню", reply_markup=main_menu())
    await callback_query.answer()


# --- МОИ ОЦЕНКИ ---
@router.callback_query(lambda c: c.data == "my_ratings")
async def my_ratings_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_feedback.setdefault(user_id, {
        "likes": [],
        "dislikes": [],
        "bookmarks": [],
        "index": 0,
        "current_category": None,
        "history": [],
        "search_results": [],
        "source": None,
        "current_index_in_list": None,
        "is_full": False,
        "recommendations": []
    })
    data = user_feedback[user_id]

    likes = get_list_reviews(user_id, 1)
    dislikes = get_list_reviews(user_id, 2)
    bookmarks = get_list_reviews(user_id, 3)

    all_rated = []
    for id in likes:
        all_rated.append(f"❤️ {Book.byID(id).name}")
    for id in dislikes:
        all_rated.append(f"💔 {Book.byID(id).name}")
    for id in bookmarks:
        all_rated.append(f"🔖 {Book.byID(id).name}")

    if not all_rated:
        text = "😶 Вы ещё не оценили ни одной книги."
    else:
        text = "📚 <b>Все ваши оценки:</b>\n\n" + "\n".join(f"{i+1}. {t}" for i, t in enumerate(all_rated))

    data["history"].append("all_ratings")
    data["last_menu"] = "ratings_all"
    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=ratings_menu_all())
    await callback_query.answer()


@router.callback_query(lambda c: c.data in ["show_likes", "show_dislikes", "show_bookmarks"])
async def show_category_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_feedback:
        init_user(user_id)

    data = user_feedback[user_id]
    user_feedback[user_id]["likes"] = get_list_reviews(user_id, 1)
    user_feedback[user_id]["dislikes"] = get_list_reviews(user_id, 2)
    user_feedback[user_id]["bookmarks"] = get_list_reviews(user_id, 3)
    data["current_category"] = callback_query.data.split("_")[1]
    data["history"].append("category_menu")
    data["source"] = "ratings"
    data["last_menu"] = "ratings_category"

    category_name = {
        "likes": "❤️ Лайки",
        "dislikes": "💔 Дизлайки",
        "bookmarks": "🔖 Закладки",
    }[data["current_category"]]
    books_list = data[data["current_category"]]

    if not books_list:
        text = f"{category_name}:\n\nПока нет книг."
    else:
        text = (
            f"{category_name}:\n\n"
            + "\n".join(f"{i+1}. {Book.byID(id).name}" for i, id in enumerate(books_list))
        )
        text += "\n\n📖 Введите номер книги, чтобы увидеть карточку."

    await callback_query.message.answer(text, parse_mode="HTML", reply_markup=ratings_menu_category())
    await callback_query.answer()



# --- ПОИСК ---
@router.callback_query(lambda c: c.data == "search_books")
async def start_search_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    init_user(user_id)
    user_feedback[user_id]["source"] = "search"
    user_feedback[user_id]["last_menu"] = "search"
    await callback_query.message.answer(
        "🔍 Введите часть названия книги для поиска:",
        reply_markup=search_menu(),
    )
    await callback_query.answer()



# --- ОБРАБОТЧИК ТЕКСТА ---
@router.message(lambda message: True)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_feedback:
        init_user(user_id)
    data = user_feedback[user_id]

    text = message.text.strip()

    # --- 1. Если уже открыта карточка (из поиска или рейтингов) ---
    if data.get("current_index_in_list") is not None:
        source = data.get("source")

        if source == "search":
            books_list = data.get("search_results", [])
        elif source == "ratings":
            category = data.get("current_category")
            books_list = data.get(category, [])
        else:
            books_list = []

        idx = data.get("current_index_in_list", 0)
        if not books_list or idx < 0 or idx >= len(books_list):
            await message.answer(
                "Сейчас открыта карточка книги.\n"
                "Пожалуйста, используйте кнопки под карточкой.",
                reply_markup=main_menu(),
            )
            return

        book_id = books_list[idx]
        book = Book.byID(book_id)
        photo = book.pic

        is_full = data.get("is_full", False)
        desc = (book.discription or "")[:MAX_FULL if is_full else MAX_SHORT]

        caption = f"<b>{book.name}</b>\nАвтор: {book.author}\n\n{desc}"

        await message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=book_keyboard_in_list(is_full=is_full),
        )
        return

    # --- 2. Если есть список и ждем номер книги (search/ratings, но карточка ещё не открыта) ---
    has_results = False
    books_list = []
    kb = None

    if data.get("source") == "search" and data.get("search_results"):
        books_list = data["search_results"]
        has_results = True
        kb = search_menu()
    elif data.get("source") == "ratings" and data.get("current_category"):
        books_list = data[data["current_category"]]
        has_results = True
        kb = ratings_menu_category()

    if has_results:
        if not text.isdigit():
            await message.answer(
                "Пожалуйста, введите ИМЕННО номер книги из списка (цифру).",
                reply_markup=kb,
            )
            return

        idx = int(text) - 1
        if not (0 <= idx < len(books_list)):
            await message.answer("❌ Неверный номер книги.", reply_markup=kb)
            return

        book_id = books_list[idx]
        data["current_index_in_list"] = idx
        data["is_full"] = False  # новая карточка -> свернуто

        if data.get("source") == "search":
            data["entry_menu"] = "search"
        elif data.get("source") == "ratings":
            data["entry_menu"] = "ratings_category"
        else:
            data["entry_menu"] = "main"

        book = Book.byID(book_id)
        photo = book.pic

        is_full = data["is_full"]
        desc = (book.discription or "")[:MAX_FULL if is_full else MAX_SHORT]

        caption = f"<b>{book.name}</b>\nАвтор: {book.author}\n\n{desc}"

        await message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=book_keyboard_in_list(is_full=is_full),
        )
        return

    # --- 3. Поиск по названию ---
    if data.get("source") == "search":
        query = text.lower()
        results = ml.search(query)
        data["search_results"] = results
        data["current_index_in_list"] = None

        if not results:
            await message.answer("❌ Ничего не найдено.", reply_markup=search_menu())
            return

        text_out = "🔍 Найдено:\n\n" + "\n".join(
            f"{i+1}. {Book.byID(id).name}" for i, id in enumerate(results)
        )
        text_out += "\n\nВведите номер книги, чтобы открыть её."

        data["last_menu"] = "search"
        await message.answer(text_out, reply_markup=search_menu())
        return

    # --- 4. Режим рейтингов (тут только номера/кнопки) ---
    if data.get("source") == "ratings" and data.get("current_category"):
        await message.answer(
            "Пожалуйста, введите номер книги из списка или используйте кнопки.",
            reply_markup=ratings_menu_category(),
        )
        return

    # --- Обработка LLM ---
    if data.get("source") == "description_search":
        await llm_send_book(message, user_id)
        return

    if data.get("source") == "llm_reply":
        await llm_reply(message, user_id)
        return

    # --- 6. Фоллбэк ---
    last_menu = data.get("last_menu", "main")

    if last_menu == "search":
        kb = search_menu()
        text_hint = "Пожалуйста, введите часть названия книги или используйте кнопки ниже."
    elif last_menu == "ratings_category":
        kb = ratings_menu_category()
        text_hint = "Пожалуйста, введите номер книги из списка или используйте кнопки ниже."
    elif last_menu == "ratings_all":
        kb = ratings_menu_all()
        text_hint = "Пожалуйста, выберите категорию оценок с помощью кнопок ниже."
    else:
        # сюда попадёт и ситуация после /start, когда пользователь просто пишет текст
        kb = main_menu()
        text_hint = "Пожалуйста, выберите действие из меню ниже."

    await message.answer(text_hint, reply_markup=kb)

@router.callback_query(lambda c: c.data == "toggle_description")
async def toggle_description_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_feedback:
        init_user(user_id)

    data = user_feedback[user_id]
    data["full_description"] = not data.get("full_description", False)

    # перерисовываем текущую карточку
    await send_book(callback_query.message, user_id, edit=True)
    await callback_query.answer()


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
        text = "🔍 Найдено:\n\n" + "\n".join(f"{i+1}. {Book.byID(id).name}" for i, id in enumerate(results))
        text += "\n\nВведите номер книги, чтобы открыть её."
        await callback_query.message.answer(text, reply_markup=search_menu())
    elif source == "ratings":
        category = data.get("current_category")
        books_list = data.get(category, [])
        category_name = {"likes": "❤️ Лайки", "dislikes": "💔 Дизлайки", "bookmarks": "🔖 Закладки"}[category]
        if not books_list:
            text = f"{category_name}:\n\nПока нет книг."
        else:
            text = f"{category_name}:\n\n" + "\n".join(f"{i+1}. {Book.byID(id).name}" for i, id in enumerate(books_list))
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
    
    likes = get_list_reviews(user_id, 1)
    dislikes = get_list_reviews(user_id, 2)
    bookmarks = get_list_reviews(user_id, 3)
    all_rated = []
    for id in likes:
        all_rated.append(f"❤️ {Book.byID(id).name}")
    for id in dislikes:
        all_rated.append(f"💔 {Book.byID(id).name}")
    for id in bookmarks:
        all_rated.append(f"🔖 {Book.byID(id).name}")
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
        data["last_menu"] = "main"

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
        data["last_menu"] = "main"

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

    book = Book.byID(books_list[idx])

    if callback_query.data == "like_no_next":
        await give_feedback(user_id, book, "like")
        msg = "❤️ Лайк"
    elif callback_query.data == "dislike_no_next":
        await give_feedback(user_id, book, "dislike")
        msg = "💔 Дизлайк"
    else:
        await give_feedback(user_id, book, "bookmark")
        msg = "🔖 В закладки"

    await callback_query.answer(msg, show_alert=False)

#--- Развертка описания ---
@router.callback_query(lambda c: c.data == "toggle_desc")
async def toggle_desc_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_feedback:
        init_user(user_id)

    data = user_feedback[user_id]

    # переключаем флаг
    data["is_full"] = not data.get("is_full", False)

    source = data.get("source")

    # если мы в списке (поиск/оценки) — перерисовываем текущую карточку из списка
    if source in ("search", "ratings") and data.get("current_index_in_list") is not None:
        if source == "search":
            books_list = data.get("search_results", [])
        else:
            category = data.get("current_category")
            books_list = data.get(category, [])
        idx = data["current_index_in_list"]
        if books_list and idx is not None and 0 <= idx < len(books_list):
            book_id = books_list[idx]
            book = Book.byID(book_id)
            photo = book.pic

            is_full = data["is_full"]
            if is_full:
                desc = (book.discription or "")[:MAX_FULL]
            else:
                desc = (book.discription or "")[:MAX_SHORT]

            caption = f"<b>{desc}</b>\n\n\n{book.name}\nАвтор: {book.author}"

            await callback_query.message.edit_media(
                media=types.InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"),
                reply_markup=book_keyboard_in_list(is_full=is_full),
            )
            await callback_query.answer()
            return

    # иначе — используем стандартную подборку (send_book)
    await send_book(callback_query.message, user_id, edit=True)
    await callback_query.answer()
