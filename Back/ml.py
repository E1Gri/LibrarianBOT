# SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True

import pandas as pd
import sqlite3
import csv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Data.book_for_tgBot import Book
from .model import LLM

def add_user_to_db(userId):
    db = sqlite3.connect("Data/DataBase.db")
    cursor = db.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("SELECT id FROM users WHERE id = ?", (userId,))
    exists = cursor.fetchone()

    if exists:
        db.close()
    else:
        cursor.execute("INSERT INTO users (id) VALUES (?)", (userId,))
        db.commit()
        db.close()
    
def get_list_reviews(userId, review: int):
        """
        return list of books ids or None
        """
        db = sqlite3.connect("Data/DataBase.db")
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("SELECT idBook FROM review WHERE idUser = ? AND esteem = ?", (userId, review))
        b = cursor.fetchall()

        db.close()

        return [r[0] for r in b]

# def get_user_id_from_db(tag: str, file_path = "Data/DataBase.db"):
#     db = sqlite3.connect(file_path)
#     cursor = db.cursor()

#     cursor.execute("SELECT * FROM users WHERE tgTag = ?", (tag,))
#     b = cursor.fetchone()

#     if b != None: 
#         db.close()
#         return b[0]
#     else: 
#         cursor.execute("INSERT INTO users (tgTag) VALUES (?)", (tag,))

#         cursor.execute("SELECT * FROM users WHERE tgTag = ?", (tag,))
#         b = cursor.fetchone()

#         db.commit()
#         db.close()

#         return int(b[0])       

class ML:
     
    def __init__(self):


        db = sqlite3.connect("Data/DataBase.db")

        cursor = db.cursor()

        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.executescript(open("Data/creation.sql", 'r').read())

        if cursor.execute("SELECT * FROM books WHERE id = ?", (1,)).fetchone() == None:

            tuples = []
            with open("Data/Combined_clean_tables.csv", 'r', encoding="utf-8") as file:
                reader = csv.DictReader(file, delimiter=';')
                for row in reader:
                    tuples.append(
                        (
                            row["name"],
                            row["author"],
                            row["date"],
                            row["genres"],
                            row["discription"],
                            row["pic"],
                            float(row["score"].replace(',', '.'))
                        )
                    )

            cursor.executemany("INSERT INTO books (name, author, year, genre, discription, picPath, score) VALUES (?, ?, ?, ?, ?, ?, ?)", tuples)
            db.commit()
            print("Books have been added to db from csv")

        self.df = pd.read_sql_query("SELECT * FROM books", db)

        self.llm = LLM()
        
        def prepare_text(row):
            author = row['author'] or ""
            genres = (row['genre'] + ", ") * 3 
            description = row['discription'] or ""
            return f"{author} {genres} {description}".lower()
        
        self.df['text'] = self.df.apply(prepare_text, axis=1)

        with open('Back/stop-ru.txt') as f:
                sw = f.read().splitlines()

        self.vectorizer = TfidfVectorizer(
            stop_words = sw,
            max_features=20000 
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['text'])

        db.close()

    def NameCossim(self, BookName: str):

        def recommend_similar(book_name, top_n=5):
            
            mask = self.df['name'].str.lower() == book_name.lower()
            if not mask.any():
                return None
            
            idx = self.df[mask].index[0]

            
            cos_sim = cosine_similarity(self.tfidf_matrix[idx], self.tfidf_matrix).flatten()

            
            similar_idxs = cos_sim.argsort()[::-1]
            similar_idxs = similar_idxs[similar_idxs != idx][:top_n]

        
            return self.df.iloc[similar_idxs][['name', 'author', 'genre', 'id', 'picPath']]


        books = recommend_similar(BookName, top_n=100)['id'].tolist()
        return books
    
    
    def GenreCossim(self, user_input: str):

        Genre = self.llm.describeGenres(user_input)

        def recommend_similar(genre, top_n=5):

            genres_list = self.df['genre'].tolist()
            
            vectorizer = TfidfVectorizer().fit(genres_list + [genre])
            tfidf_matrix = vectorizer.transform(genres_list + [genre])
            
            cos_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
            
            top_idxs = cos_sim.argsort()[::-1][:top_n]

            return self.df.iloc[top_idxs][['name', 'author', 'genre', 'id', 'picPath']]

        books = recommend_similar(Genre, top_n=100)['id'].tolist()
        return books


    def Likes(self, UserId: int):
        db = sqlite3.connect("Data/DataBase.db")
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("SELECT * FROM review WHERE idUser = ? AND esteem = ?", (UserId, 1))
        b = cursor.fetchall()

        db.close()

        likes = get_list_reviews(UserId, 1)

        lists = []

        for id in likes:
            theBook = Book.byID(id)
            lists += self.NameCossim(theBook.name)

        return list(set(lists))
    
    def recommendations(self, UserId: int, ):
        """
        Надо еще будет фичей добавить
        """

        default_reccomendations = [217, 23099, 2726, 3511, 29786, 23256, 23371, 21, 611, 26906]

        likes = get_list_reviews(UserId, 1)
        dislikes = get_list_reviews(UserId, 2)
        saved = get_list_reviews(UserId, 3)
        seen = get_list_reviews(UserId, 0)

        #Фича 1 Ркекоммендации на основе лайков пользователя
        booksId = self.Likes(UserId)
        booksId = list(set(default_reccomendations +  booksId))
        result = []

        for i in range(len(booksId)):
            if booksId[i] in dislikes or booksId[i] in saved or booksId[i] in seen or booksId[i] in likes:
                continue
            else:
                result.append(booksId[i])
                
        
        return result
    
    @staticmethod
    def search(bookName: str, file_path="Data/DataBase.db", limit=10):
        db = sqlite3.connect(file_path)
        cursor = db.cursor()

        cursor.execute("SELECT id, name FROM books")
        rows = cursor.fetchall()
        db.close()

        query = bookName.strip().lower()
        books_found = []

        for row in rows:
            book_id, book_name = row
            if query in book_name.strip().lower():
                books_found.append(book_id)
                if len(books_found) >= limit:
                    break

        return books_found
    
    def llm_recommendations(self, UserId, UserInput):
        dislikes = get_list_reviews(UserId, 2)
        saved = get_list_reviews(UserId, 3)
        seen = get_list_reviews(UserId, 0)

        books = self.GenreCossim(UserInput)

        for i in books:
            if i in dislikes or i in saved or i in seen:
                books.pop(i)

        return books
    

