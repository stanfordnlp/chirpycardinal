from .integration_base import BaseIntegrationTest
from parameterized import parameterized
from chirpy.annotators.corenlp import Sentiment


class TestCoreNLP(BaseIntegrationTest):

    def test_corenlp(self):
        """Check that the corenlp output matches what we expect for an example utterance"""
        _, current_state, response_text = self.init_and_first_turn('serena williams is the best tennis player ever')
        self.assertSetEqual(set(current_state['corenlp']['ner_mentions']), {('serena williams', 'PERSON'), ('tennis player', 'TITLE')})
        self.assertEqual(current_state['corenlp']['sentiment'], Sentiment.POSITIVE)
        self.assertSetEqual(set(current_state['corenlp']['nounphrases']), {'serena williams', 'the best tennis player'})
        self.assertSetEqual(set(current_state['corenlp']['verbphrases']), {'is the best tennis player ever'})
        self.assertSetEqual(set(current_state['corenlp']['proper_nouns']), {'serena williams'})
        self.assertSetEqual(set(current_state['corenlp']['nouns']), {'tennis', 'player'})
