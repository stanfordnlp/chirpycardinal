from .integration_base import BaseIntegrationTest
from chirpy.response_generators.one_turn_hack_response_generator import one_turn_responses
from random import uniform
from parameterized import parameterized

class OneTurnHackResponseGenerator(BaseIntegrationTest):

    launch_sequence = ['let\'s chat', 'my name is jamie', 'pretty good and you', 'books', 'supernova']
    @parameterized.expand(one_turn_responses.items())
    def test_several_phrases_affirmative_response(self, utterance, response):
        if uniform(0, 1) < 0.5:
            utterance = "alexa " + utterance
        _, current_state, response_text = self.process_utterance(utterance)
        expected_response_text, needs_prompt = response
        self.assertIn(expected_response_text, response_text)

