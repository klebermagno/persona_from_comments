import re
import string


class TextCleaner:
    def __init__(self):
        self.link_regex = re.compile(
            "((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)", re.DOTALL
        )
        self.entity_prefixes = ["@", "#"]
        self.punctuation_translator = str.maketrans("", "", string.punctuation)
        self.entities_translator = str.maketrans("", "", "@#")

    def strip_links(self, text):
        links = re.findall(self.link_regex, text)
        for link in links:
            text = text.replace(link[0], "")
        return text

    def strip_punctuation(self, text):
        return text.translate(self.punctuation_translator).strip()

    def strip_entities(self, text):
        """
        Remove basic entities like #hashtags, @mentions
        Future: $symbols, URLs, and media.
        """
        words = []
        for word in text.split():
            word = word.strip()
            if word:
                if word[0] not in self.entity_prefixes:
                    words.append(word)
        return " ".join(words)

    def clean_entities_symbols(self, text):
        """
        Remove # and @ from entities.
        """
        return text.translate(self.entities_translator).strip()

    def clean_symbols_from_entities(self, text):
        """
        Remove # and @ from entities.
        """
        words = []
        for word in text.split():
            word = word.strip()
            if word:
                if word[0] in self.entity_prefixes:
                    words.append(word[1:])
                else:
                    words.append(word)
        return " ".join(words)

    def strip_entities_links(self, text):
        """
        Example:
            input: @daniel I want that camera at #Bestbuy. http://bit.ly//WR4Rt
            output: I want that camera at
        """
        return self.strip_entities(self.strip_links(text))
