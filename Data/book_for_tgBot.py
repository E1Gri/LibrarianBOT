import pandas as pd
import sqlite3

class Book:
    def __init__(self):
        self.name = None
        self.author = None
        self.date = None
        self.discription = None
        self.genres = None
        self.pic = None
        self.url = None
        self.score = None
    
    def get_from_csv(self, line_number, file_path="Data/Combined_clean_tables.csv"):
        try:
            df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            # row = df.iloc[row_number]
            if line_number < 1 or line_number > len(df):
                print(f"Строка {line_number} вне диапазона (1-{len(df)})")
                return self
                
            data_index = line_number - 1
            line = df.iloc[data_index]
            
            self.name = line.get('name')
            self.author = line.get('author')
            self.date = line.get('date')
            self.discription = line.get('discription')
            self.genres = line.get('genres')
            self.pic = line.get('pic')
            self.url = line.get('url')
            self.score = line.get('score')
            
            print(f"Книга '{self.name}' загружена из строки {line_number}")
            
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
    
    def display_info(self):
        if self.name:
            print('\n' + f"{self.name} | {self.author} | {self.date}  | Score: {self.score}" + '\n')
            print(f"Description: {self.discription}" + '\n')
            print(f"Genres: {self.genres}" + '\n')
            print(f"pic: {self.pic}" + '\n')
            if self.url != None: print(f"URL: {self.url}" + '\n')
        else:
            print("Книга не загружена")

    def get_tuple(self):
        if self.name != None:
            return (self.name, self.author, self.date, self.genres, self.discription, self.pic, self.score)


    def get_from_sql(self, id: int, file_path = "Data/DataBase.db"):
        db = sqlite3.connect(file_path)
        cursor = db.cursor()

        cursor.execute("SELECT * FROM books WHERE id = ?", (id,))
        b = cursor.fetchone()

        if b != None:
            self.id = id
            self.name =         b[1]
            self.author =       b[2]
            self.genres =       b[3]
            self.date =         b[4]
            self.discription =  b[5]
            self.pic =          b[6]
            self.score =        b[7]
        
        db.close()
    
    def byID(bd_id: int, file_path = "Data/DataBase.db"):
        """
        book by id in bd
        """
        book = Book()
        book.url = None
        book.get_from_sql(bd_id, file_path)
        return book
    
    def findReview(self, idUser: int,  file_path = "Data/DataBase.db"):
        db = sqlite3.connect(file_path)
        cursor = db.cursor()

        cursor.execute("SELECT esteem FROM review WHERE idBook = ? AND idUser = ?", (self.id, idUser))
        b = cursor.fetchone()
        db.close()

        if b != None:
            return int(b[0])
        else:
            return None


    def review(self, id_user: int, user_input: int,  file_path = "Data/DataBase.db"):
        """
        user_input: 
        0 - seen,
        1 - like,
        2 - dislike,
        3 - saved
        """

        if user_input < 0 or user_input > 3:
            user_input = 0

        reviewExist = self.findReview(id_user)

        db = sqlite3.connect(file_path)
        cursor = db.cursor()
        db.execute("PRAGMA foreign_keys = ON")

        if reviewExist == None:
            cursor.execute("INSERT INTO review (idBook, idUser, esteem) VALUES (?, ?, ?)", (self.id, id_user, user_input))
        else:
            cursor.execute("UPDATE review SET esteem = ? WHERE idBook = ? AND idUser = ?", (user_input, self.id, id_user))

        db.commit()
        db.close()




 