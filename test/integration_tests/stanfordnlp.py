from .integration_base import BaseIntegrationTest
from parameterized import parameterized


class TestStanfordNLP(BaseIntegrationTest):

    def test_stanfordnlp(self):
        """
        Check that the stanfordnlp output matches what we expect for an example utterance.
        This test just checks that the module ran and the output is the same as usual.
        These stanfordnlp outputs don't really seem right. We should look at how the postprocessing code is getting these outputs.
        """
        _, current_state, response_text = self.init_and_first_turn('serena williams is the best tennis player ever')
        self.assertSetEqual(set(current_state['stanfordnlp']['nouns']), {'player'})
        self.assertSetEqual(set(current_state['stanfordnlp']['nounphrases']), {'serena williams is the best tennis player ever'})
        self.assertSetEqual(set(current_state['stanfordnlp']['proper_nouns']), {'serena williams'})