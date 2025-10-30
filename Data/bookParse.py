import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv

table_name = str(input("Введите название таблицы: "))

# with open(table_name + ".csv", "w", newline="", encoding="utf-8-sig") as file:
#     writer = csv.writer(file, delimiter=';')
#     writer.writerow(["name", "author", "date", "discription", "genres", "pic", "url", "score"])
#     file.close

url = str(input("Введите ссылку на каталог: "))

params = {
    "languages": "ru",
    "art_types": "text_book",
    "page": "0"
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

pages = int(input("Введите кол-во страниц, которое нужно просмотреть: "))

for page in range(486, pages+1):
    params["page"] = str(page)

    response = requests.get(url, headers=headers, params=params)

    soup = BeautifulSoup(response.text, "html.parser")

    books_urls = []

    divs = soup.find_all("div", class_=["baf48440", "b01c802a"])

    for div in soup.select('div[data-testid="art__wrapper"]'):
        a_tag = div.find("a", href=True)
        if a_tag:
            full_url = urljoin("https://www.litres.ru", a_tag["href"])
            books_urls.append(full_url)

    for book in books_urls:
        response = requests.get(book)
        soup = BeautifulSoup(response.text, "html.parser")
        spans= soup.find_all("span")

        #namesoup = soup.find("h1", class_ = ["_8dfa70c8", "ed20f469"])
        namesoup = soup.find("h1")
        if namesoup == None:
            continue
        name = namesoup.getText()
        

        author = spans[2].get_text(strip=True)
        
        date = ''
        for i in range(1, len(spans)):
            if spans[i].get_text(strip=True) == "Дата написания:":
                date = spans[i+1].get_text()

        discription = ''
        dscrp = soup.find("div", class_ = ["ac83cc29"],)
        for p in dscrp:
            discription += p.get_text()
        
        genres = soup.find("div", class_ = "aa63d864").get_text(strip = 1)

        pic = soup.find("div", class_ = ["_0bd8490c", "_78d816e0"])
        pic = pic.find("img")
        pic = pic.get("src")

        scoresoup = soup.find("div", class_ ="_1419d759")
        score = scoresoup.get_text()

        with open(table_name + '.csv', "a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow([name, author, date, discription, genres, pic, book, score])

    print("Отсканированно страниц: ", page)
