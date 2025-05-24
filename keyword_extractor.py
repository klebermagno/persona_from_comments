from rake_nltk import Rake
import yake
import spacy


class KeywordExtractor:

    def get_rake_keywords(self, text):
        rake_nltk_var = Rake(
            language="english",
            include_repeated_phrases=False,
            min_length=2,
            max_length=4,
        )
        rake_nltk_var.extract_keywords_from_text(text)
        keyword_extracted = rake_nltk_var.get_ranked_phrases_with_scores()

        top = 10
        keywords = []
        for word in keyword_extracted:
            keywords.append(word[1])
            top -= 1
            if top <= 0:
                break
        return keywords

    # the best one
    def get_yake_keywords(self, text):
        language = "en"
        max_ngram_size = 3
        deduplication_threshold = 0.8
        deduplication_algo = "seqm"
        windowSize = 1
        numOfKeywords = 40

        custom_kw_extractor = yake.KeywordExtractor(
            lan=language,
            n=max_ngram_size,
            dedupLim=deduplication_threshold,
            dedupFunc=deduplication_algo,
            windowsSize=windowSize,
            top=numOfKeywords,
            features=None,
        )
        keywords = custom_kw_extractor.extract_keywords(text)
        return keywords

    def get_spacy_keyword(self, text):
        nlp = spacy.load("en_core_news_sm")
        doc = nlp(text)

        return [ent for ent in doc.ents]
