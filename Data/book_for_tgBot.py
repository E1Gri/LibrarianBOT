import pandas as pd

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
    
    def get_from_csv(self, line_number, file_path="Combined_clean_tables.csv"):
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
            print(f"{self.name} | {self.author} | {self.date} | {self.discription} | {self.genres} | {self.pic} | {self.url} | {self.score}")
        else:
            print("Книга не загружена")


book = Book()
book.get_from_csv(1)  
book.display_info()  