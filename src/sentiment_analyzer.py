from .text_cleaner import TextCleaner
from textblob import TextBlob
from langdetect import detect


class SentimentAnalyser:
    """
    This method works only for english
    """

    def __init__(self):
        self.text_cleaner = TextCleaner()

    def _strip(self, text):
        return self.text_cleaner.clean_entities_symbols(
            self.text_cleaner.strip_links(text)
        )

    def get_language(self, text):
        return detect(text)

    def sentiment(self, text):
        text = self._strip(text)
        t = TextBlob(text)
        return t.sentiment.polarity

    def get_most_sentimental_sentence(self, text, is_negative=False):
        blob = TextBlob(text)

        intensity = 0
        intense_sentence = ""
        for sentence in blob.sentences:
            score = sentence.sentiment.polarity
            if is_negative:
                if score < intensity:
                    intense_sentence = str(sentence)
                    intensity = score
            else:
                if score > intensity:
                    intense_sentence = str(sentence)
                    intensity = score
        return intense_sentence

    def _round_polarity(self, polarity):
        if polarity < -0.25:
            return -1
        elif polarity > 0.25:
            return 1
        else:
            return 0
