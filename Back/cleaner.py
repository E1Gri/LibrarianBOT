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
    file = open("stop-ru.txt", "r")

    for i in file:
        russian_stopwords.append(i[:-1])

    morph = pymorphy2.MorphAnalyzer()

    text = text.lower()


    translator = str.maketrans('', '', string.punctuation + '0123456789')
    text_cleaned = text.translate(translator)


    tokens = [token.text for token in tokenize(text_cleaned)]

    tokens = [t for t in tokens if t not in russian_stopwords]


    lemmas = [morph.parse(t)[0].normal_form for t in tokens]

    return lemmas


