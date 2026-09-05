import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer


def download_nltk_dependencies():
    """
    Safely download necessary NLTK datasets if not already available locally.
    """
    for resource in ["stopwords", "punkt", "wordnet", "omw-1.4"]:
        try:
            nltk.data.find(f"corpora/{resource}")
        except LookupError:
            try:
                nltk.data.find(f"tokenizers/{resource}")
            except LookupError:
                nltk.download(resource, quiet=True)


class TextPreprocessor:
    """
    NLP Preprocessing pipeline for full-article text classification.
    Includes lowercasing, URL/HTML stripping, regex cleaning,
    stopword filtering, and optional stemming or lemmatization.
    """

    def __init__(self, use_stemming: bool = True, use_lemmatization: bool = False):
        download_nltk_dependencies()
        self.stop_words = set(stopwords.words("english"))
        self.stemmer = PorterStemmer() if use_stemming else None
        self.lemmatizer = WordNetLemmatizer() if use_lemmatization else None

    def clean_text(self, text: str) -> str:
        """
        Applies cleaning transformations to raw news text string.
        """
        if not text or not isinstance(text, str):
            return ""

        # 1. Lowercasing
        text = text.lower()

        # 2. Remove URLs and domain links
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)

        # 3. Remove HTML tags
        text = re.sub(r"<.*?>", " ", text)

        # 4. Remove emails
        text = re.sub(r"\S+@\S+", " ", text)

        # 5. Keep only alphabetic characters and replace non-alphabetic characters with space
        text = re.sub(r"[^a-zA-Z\s]", " ", text)

        # 6. Tokenize & Filter Stopwords + Apply Stemming/Lemmatization
        words = text.split()
        filtered_words = []
        for word in words:
            if word not in self.stop_words and len(word) > 2:
                if self.stemmer:
                    word = self.stemmer.stem(word)
                elif self.lemmatizer:
                    word = self.lemmatizer.lemmatize(word)
                filtered_words.append(word)

        # 7. Rejoin tokens into a cleaned string
        return " ".join(filtered_words)

    def preprocess_corpus(self, corpus: list[str]) -> list[str]:
        """
        Preprocess a collection of text articles.
        """
        return [self.clean_text(doc) for doc in corpus]
