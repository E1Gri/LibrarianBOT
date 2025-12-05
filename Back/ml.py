import sqlite3
import csv
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from .cleaner import tclean
from .model import LLM
import numpy as np
from Back.cleaner_object import thisDirtyTextNeedsToBe
from sklearn.preprocessing import normalize

# ====== Функции для работы с БД ======
def add_user_to_db(userId):
    db = sqlite3.connect("Data/DataBase.db")
    cursor = db.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("SELECT id FROM users WHERE id = ?", (userId,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (id) VALUES (?)", (userId,))
        db.commit()
    db.close()


def get_list_reviews(userId, review: int):
    db = sqlite3.connect("Data/DataBase.db")
    cursor = db.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("SELECT idBook FROM review WHERE idUser = ? AND esteem = ?", (userId, review))
    b = cursor.fetchall()
    db.close()
    return [r[0] for r in b]


# ===== Основной ML-класс =====
class ML:
    def __init__(self):
        db = sqlite3.connect("Data/DataBase.db")
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # загружаем csv если таблица пустая
        cursor.executescript(open("Data/creation.sql", 'r').read())
        if cursor.execute("SELECT * FROM books WHERE id = 1").fetchone() is None:
            tuples = []
            with open("Data/Combined_clean_tables.csv", 'r', encoding="utf-8") as file:
                reader = csv.DictReader(file, delimiter=';')
                for row in reader:
                    tuples.append((
                        row["name"], row["author"], row["date"], row["genres"],
                        row["discription"], row["pic"],
                        float(row["score"].replace(',', '.'))
                    ))
            cursor.executemany("""
                INSERT INTO books (name, author, year, genre, discription, picPath, score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, tuples)
            db.commit()

        # загружаем dataframe
        self.df = pd.read_sql_query("SELECT * FROM books", db)
        db.close()

        self.llm = LLM()

        # ====== ЭМБЕДДЕР ======
        
        # mode = "fast"
        mode = "slow"

        if mode == "fast":
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
            try:
                self.embeddings = np.load("Data/Fastembeddings.npy")
                print("Эмбеддинги загружены с диска.")
            except FileNotFoundError:
                print("создаём поле с текстом для embedding")
                def prepare_text(row):
                    author = row['author'] or ""
                    genres = (row['genre'] + ", ") * 3
                    description = thisDirtyTextNeedsToBe.cleaned(row['discription']) or ""
                    return f"{row['name']} {author} {genres} {description}".lower()
                self.df["text"] = self.df.apply(prepare_text, axis=1)
                
                print("Генерация эмбеддингов для всех книг...")
                self.embeddings = self.embedder.encode(self.df["text"].tolist(), show_progress_bar=True)
                self.embeddings = normalize(self.embeddings, axis=1)
                np.save("Data/Fastembeddings.npy", self.embeddings)
                print("Эмбеддинги сохранены на диск.")            


        elif mode == "slow":
            self.embedder = SentenceTransformer("all-mpnet-base-v2")
            try:
                self.embeddings = np.load("Data/Slowembeddings.npy")
                print("Эмбеддинги загружены с диска.")
            except FileNotFoundError:
                print("создаём поле с текстом для embedding")
                def prepare_text(row):
                    author = row['author'] or ""
                    genres = (row['genre'] + ", ") * 3
                    description = thisDirtyTextNeedsToBe.cleaned(row['discription']) or ""
                    return f"{row['name']} {author} {genres} {description}".lower()
                self.df["text"] = self.df.apply(prepare_text, axis=1)
                
                print("Генерация эмбеддингов для всех книг...")
                self.embeddings = self.embedder.encode(self.df["text"].tolist(), show_progress_bar=True)
                self.embeddings = normalize(self.embeddings, axis=1)
                np.save("Data/Slowembeddings.npy", self.embeddings)
                print("Эмбеддинги сохранены на диск.")


    # ----------- COS-SIM по названию ----------
    def NameCossim(self, BookName: str):
        mask = self.df['name'].str.lower() == BookName.lower()
        if not mask.any():
            return []

        idx = self.df[mask].index[0]

        q_vec = self.embeddings[idx].reshape(1, -1)
        sims = cosine_similarity(q_vec, self.embeddings).flatten()

        top_idx = sims.argsort()[::-1]
        top_idx = top_idx[top_idx != idx][:100]

        return self.df.iloc[top_idx]["id"].tolist()

    def DescCossim(self, user_description: str):
        user_description = tclean(user_description)

        query_vec = self.embedder.encode([user_description], convert_to_numpy=True)
        query_vec = normalize(query_vec, axis=1)

        sims = cosine_similarity(query_vec, self.embeddings).flatten()

        top_idx = sims.argsort()[::-1]

        return self.df.iloc[top_idx[:100]]["id"].tolist()
        

    # ----------- COS-SIM по жанру -------------
    def GenreCossim(self, user_input: str):
        genre_text = self.llm.describeGenres(user_input)
        q_vec = self.embedder.encode([genre_text])

        sims = cosine_similarity(q_vec, self.embeddings).flatten()
        top_idx = sims.argsort()[::-1][:100]

        return self.df.iloc[top_idx]["id"].tolist()

    # ----------- Рекомендации на основе лайков --------
    def Likes(self, UserId: int):
        likes = get_list_reviews(UserId, 1)
        result = []

        for book_id in likes:
            name = self.df.loc[self.df["id"] == book_id, "name"].values[0]
            result += self.NameCossim(name)

        return list(set(result))

    # ----------- Итоговые рекомендации ----------
    def recommendations(self, UserId: int):
        default_reccomendations = [217, 23099, 2726, 3511, 29786, 23256, 23371, 21, 611, 26906]

        likes = get_list_reviews(UserId, 1)
        dislikes = get_list_reviews(UserId, 2)
        saved = get_list_reviews(UserId, 3)
        seen = get_list_reviews(UserId, 0)

        books = list(set(default_reccomendations + self.Likes(UserId)))

        result = []
        for book_id in books:
            if book_id not in dislikes and book_id not in saved and book_id not in seen and book_id not in likes:
                result.append(book_id)

        return result

    # ----------- Поиск книги в БД -----------
    @staticmethod
    def search(bookName: str, file_path="Data/DataBase.db", limit=10):
        db = sqlite3.connect(file_path)
        cursor = db.cursor()
        cursor.execute("SELECT id, name FROM books")
        rows = cursor.fetchall()
        db.close()

        query = bookName.lower().strip()
        out = []

        for book_id, name in rows:
            if query in name.lower():
                out.append(book_id)
                if len(out) >= limit:
                    break
        return out

    # ----------- LLM рекомендации ----------
    def llm_recommendations(self, UserId, UserInput):
        dislikes = get_list_reviews(UserId, 2)
        saved = get_list_reviews(UserId, 3)
        seen = get_list_reviews(UserId, 0)

        books = self.GenreCossim(UserInput)
        result = []

        for b in books:
            if b not in dislikes and b not in saved and b not in seen:
                result.append(b)

        return result
