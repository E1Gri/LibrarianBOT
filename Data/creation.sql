CREATE TABLE IF NOT EXISTS users 
( 
    id INTEGER PRIMARY KEY,
    indx INTEGER,
    currentCategory TEXT,
    source TEXT,
    favAuthor TEXT,
    favGenre TEXT
);
 
CREATE TABLE IF NOT EXISTS books
( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    author TEXT,
    genre TEXT,
    year INTEGER,
    discription TEXT, 
    picPath TEXT, 
    score FLOAT 
); 

CREATE TABLE IF NOT EXISTS review
 ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idBook INTEGER NOT NULL,
    idUser INTEGER NOT NULL,
    esteem INTEGER NOT NULL, -- 0 - seen, 1 - like, 2 - dislike, 3 - saved 
    FOREIGN KEY (idBook) REFERENCES books(id) ON DELETE CASCADE, 
    FOREIGN KEY (idUser) REFERENCES users(id) ON DELETE CASCADE 
 );