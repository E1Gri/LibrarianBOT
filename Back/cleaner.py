import string
import nltk
import pymorphy2
from razdel import tokenize
from nltk.corpus import stopwords


# nltk.download('punkt_tab')
# nltk.download('stopwords')

# nltk.download()


def tclean(text):
    russian_stopwords = []
    file = open("Back/stop-ru.txt", "r")

    for i in file:
        russian_stopwords.append(i[:-1])

    morph = pymorphy2.MorphAnalyzer()

    text = text.lower()


    translator = str.maketrans('', '', string.punctuation + '0123456789')
    text_cleaned = text.translate(translator)


    tokens = [token.text for token in tokenize(text_cleaned)]

    tokens = [t for t in tokens if t not in russian_stopwords]


    lemmas = [morph.parse(t)[0].normal_form for t in tokens]

    return " ".join(lemmas)

class textCleaner():

    def __init__(self):
        self.russian_stopwords = []

        file = open("Back/stop-ru.txt", "r")

        for i in file:
            self.russian_stopwords.append(i[:-1])

        self.morph = pymorphy2.MorphAnalyzer()
        
        self.translator = str.maketrans('', '', string.punctuation + '0123456789')
    
    def cleaned(self, text):
        text = text.lower()

        text_cleaned = text.translate(self.translator)

        tokens = [token.text for token in tokenize(text_cleaned)]

        tokens = [t for t in tokens if t not in self.russian_stopwords]


        lemmas = [self.morph.parse(t)[0].normal_form for t in tokens]

        return " ".join(lemmas)