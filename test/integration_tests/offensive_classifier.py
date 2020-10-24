from .integration_base import BaseIntegrationTest
from parameterized import parameterized
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.entity_linker.lists import STOPWORDS

class TestOffensiveClassifier(BaseIntegrationTest):

    @parameterized.expand(['fuck', 'fuck you', 'you fuck', 'alexa fuck you', 'FuCk', 'fucks', "fuck's", "fuck'll",
                           'fuck-day', 'i said...fuck!', 'f**k', 'f#@k'])
    def test_offensive(self, user_utterance):
        """
        Check that the offensive classifier recognizes offensive phrases, robust to case, singular/plural, punctuation,
        position in text, etc.
        """
        self.assertTrue(contains_offensive(user_utterance))

    def test_stopwords_inoffensive(self):
        """
        Check that the offensive classifier doesn't classify any stopwords as offensive.
        This isn't a comprehensive check for false positives, but it checks for the most common inoffensive words.
        """
        self.assertFalse(contains_offensive(' '.join(STOPWORDS)))

    def test_added_phrases(self):
        """
        Check that the offensive classifier recognizes manually added offensive phrases
        """
        self.assertTrue(contains_offensive("i'm watching pornhub"))

    def test_removed_phrases(self):
        """
        Check that the offensive classifier doesn't recognize manually removed phrases
        """
        self.assertFalse(contains_offensive("i love ginger cake"))

    def test_whitelist(self):
        """
        Check that the offensive classifier doesn't recognize phrases in the whitelist but still recognizes offensive
        phrases elsewhere in the text
        """
        self.assertFalse(contains_offensive("have you seen kill bill"))
        self.assertTrue(contains_offensive("fuck have you seen kill bill"))


