from .integration_base import BaseIntegrationTest
from parameterized import parameterized

class TestOffensiveUserResponseGenerator(BaseIntegrationTest):
    launch_sequence = ['let\'s chat']

    def test_offensive_utterance(self):
        """Check that OFFENSIVE_USER RG responds to an offensive user utterance"""
        for user_utterance in ['fuck you alexa']:
            self.reset_ask_to_post_launch_sequence()
            _, current_state, response_text = self.process_utterance(user_utterance)
            self.assertEqual(current_state['selected_response_rg'], 'OFFENSIVE_USER')

    @parameterized.expand(['fuck no', 'yes bitch'])
    def test_offensive_yesno(self, user_utterance):
        """Check that OFFENSIVE_USER RG doesn't respond to an offensive yes/no utterance"""
        self.reset_ask_to_post_launch_sequence()
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertNotEqual(current_state['selected_response_rg'], 'OFFENSIVE_USER')

    @parameterized.expand(['you suck alexa', "what's wrong with you"])
    def test_critical_utterance(self, user_utterance):
        """Check that OFFENSIVE_USER RG responds to user criticism appropriately"""
        self.reset_ask_to_post_launch_sequence()
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertEqual(current_state['selected_response_rg'], 'OFFENSIVE_USER')

    @parameterized.expand(['i watched hell\'s kitchen', 'there was a movie called hitler\'s demise', 'i like to watch sex education'])
    def test_no_response(self, user_utterance):
        """Check that OFFENSIVE_USER RG not respond appropriately"""
        self.reset_ask_to_post_launch_sequence()
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertNotEqual(current_state['selected_response_rg'], 'OFFENSIVE_USER')