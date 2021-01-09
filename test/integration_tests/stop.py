from .integration_base import BaseIntegrationTest
from parameterized import parameterized


class TestStoppingWords(BaseIntegrationTest):
    launch_sequence = ['let\'s chat', 'my name is leland']

    @parameterized.expand(['shut off', 'cancel', 'off', 'alexa off', 'be quiet', 'end chat',
                           'can you please stop', 'leave me alone', 'pause'])
    def test_stop(self, phrase):
        alexa_response, _, _ = self.process_utterance(phrase)
        self.assertTrue(alexa_response['response']['shouldEndSession'])