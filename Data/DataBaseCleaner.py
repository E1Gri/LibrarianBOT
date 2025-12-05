"""
Чистка мусорных патернов из описания книг
 в базе данных
Так же реализован кусочек кода,
 который выводит книгу по айди
 и демонстрирует ее описание
 (сделано для самопроверки)
 
(Поиск книг в базе данных с мусорными 
 паттернами в описании 
И еализована запись айди книг
 с мусором в описании в отдельный файл) - НЕ АКТУАЛЬНО
"""

import sqlite3
import re
from book_for_tgBot import Book  

input_file = "DataBase.db" 
output_file = "bad_books_ids.txt"  

bad_patterns = [     
    r'доступен по подписке.*',  
    r'для чтения книги не обязательно.*',
    r'продолжить читать или слушать произведение с того места.*',  
    r'Теперь и бумажные книги.*',  
    r'иПереиздания.*'
    r'икниги.*', 
    r'читать на ЛитРес.*',         
    r'ЛитРес.*',                       
    r'₽.*',
    r'Другие версии.*',
    r'Синхронизировано.*',
    r'аудио книг.*',
    r'аудиокнига.*',
    r'аудио.*',  
    r'https?://\S+.*',              
    r'Читает.*',
    r'с текстовой версией.*',
    r'В этой версии книги вы можете с легкостью переключиться.*',
    r'переключиться с электронной на версию.*',            
]

bad_book_ids = [] 

# print("\nИщем книги с мусором")

# try:
#     db = sqlite3.connect(input_file)
#     cursor = db.cursor()
#     cursor.execute("SELECT id FROM books")
#     all_ids = [row[0] for row in cursor.fetchall()]
#     db.close()

# except Exception as e:
#     print(f"Ошибка при обработке файла {input_file}: {e}")

# for book_id in all_ids:
#     try:
#         book = Book.byID(book_id, input_file)

#         if book is None or book.discription is None:  # проверяем НА ВСЯКИЙ СЛУЧАЙ удалось ли загрузить книгу
#             continue  

#         discription = book.discription
#         has_trash = False

#         for pattern in bad_patterns:
#             if re.search(pattern, discription, re.IGNORECASE):
#                 has_trash = True
#                 break 

#         if has_trash:
#             bad_book_ids.append(book_id)

#     except Exception as e:
#         print(f"Ошибка при обработке книги {book_id}: {e}")

# if bad_book_ids:
#     with open(output_file, 'w', encoding='utf-8') as f:
#         for book_id in bad_book_ids:
#             f.write(str(book_id) + '\n')
#     print(f"\nНашли {len(bad_book_ids)} книг с мусором в описании")
#     print(f"Айди книг сохранены в файл: {output_file}")
# else:
#     print("\nНе нашли ни одной книги с мусором в описании (они ееесть)")

# print("Ураа поиск завершён!")

print("\nЧистим книги от мусора")

try:
    db_clean = sqlite3.connect(input_file)
    cursor_clean = db_clean.cursor()

    cleaned_count = 0

    for book_id in bad_book_ids:
        try:
            book = Book.byID(book_id, input_file)

            original_disc = book.discription
            cleaned_disc = original_disc

            for pattern in bad_patterns:
                cleaned_disc = re.sub(pattern, '', cleaned_disc, flags=re.IGNORECASE | re.DOTALL)

            cleaned_disc = re.sub(r'\s+', ' ', cleaned_disc).strip()

            if cleaned_disc != original_disc:
                cursor_clean.execute("UPDATE books SET discription = ? WHERE id = ?", (cleaned_disc, book_id))
                db_clean.commit()
                cleaned_count += 1

        except Exception as e:
            print(f"Ошибка при обработке книги {book_id}: {e}")

    db_clean.close()
    print(f"\nОбработано: {len(bad_book_ids)} книг\nOчищено: {cleaned_count} книг")

except Exception as e:
    print(f"Ошибка при подключении к БД: {e}")

print("\nПочистили!\n")

print("=" * 40)

print("\nЧекаем че внутри")

while True:
    user_input = input("\nВведи айди книги (или 0 чтоб выйти): ").strip()
    if user_input == "0":
        print("Пока пока!")
        break

    book_id = int(user_input)
    book = Book.byID(book_id, input_file)

    if book is None:
        print(f"Книга с айди {book_id} не найдена(")
    else:
        print(f"\nОписание книги {book_id}:")
        print("-" * 40)
        print(book.discription)
        print("-" * 40)