# SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True

import pandas as pd
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from book_for_tgBot import Book
from model import LLM

def get_list_reviews(userId, review: int):
        """
        return list of books ids or None
        """
        db = sqlite3.connect("DataBase.db")
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("SELECT idBook FROM review WHERE idUser = ? AND esteem = ?", (userId, review))
        b = cursor.fetchall()

        db.close()

        return [r[0] for r in b]
        

class ML:
     
    def __init__(self):
        db = sqlite3.connect("DataBase.db")

        cursor = db.cursor()

        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.executescript(open("creation.sql", 'r').read())

        if cursor.execute("SELECT * FROM books WHERE id = ?", (1,)).fetchone() == None:

            tuples = []
            with open("Combined_clean_tables.csv", 'r', encoding="utf-8") as file:
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
            print("Books have been added to db from csv")

        self.df = pd.read_sql_query("SELECT * FROM books", db)
        
        def prepare_text(row):
            author = row['author'] or ""
            genres = (row['genre'] + ", ") * 3 
            description = row['discription'] or ""
            return f"{author} {genres} {description}".lower()
        
        self.df['text'] = self.df.apply(prepare_text, axis=1)

        with open('stop-ru.txt') as f:
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


        books = recommend_similar(BookName, top_n=100)
        return books
    
    
    def GenreCossim(self, Genre: str):

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
        db = sqlite3.connect("DataBase.db")
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("SELECT * FROM review WHERE idUser = ? AND esteem = ?", (UserId, 1))
        b = cursor.fetchall()

        db.close()

        likes = []
        for book in b:
            likes.append(book[1])

        lists = []

        for id in likes:
            theBook = Book.byID(id)
            lists += self.NameCossim(theBook.name)['id'].to_list()

        return list(set(lists))


        