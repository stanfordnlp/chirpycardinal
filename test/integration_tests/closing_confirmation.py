from parameterized import parameterized
from .integration_base import BaseIntegrationTest

class TestClosingConfirmation(BaseIntegrationTest):
    launch_sequence = ['let\'s chat', 'yes', 'alexa i\'m done for now']

    # change to test if confirmation
    def test_confirm_closing_high(self):
        """Check that the closing confirmation is selected when closing is predicted with high confidence"""
        _, _, _ = self.init_and_first_turn("let's chat")
        alexa_response, current_state, _ = self.process_utterance("let's end the conversation")
        self.assertTrue(current_state['dialog_act']['probdist']['closing'] > 0.9)
        self.assertEqual(current_state['selected_response_rg'], 'CLOSING_CONFIRMATION')

    
    @parameterized.expand(["i think we\'re done for now"])
    def test_confirm_closing_moderate(self, user_utterance):
        """Check that closing confirmation is selected when closing is predicted with moderate confidence"""
        _, _, _ = self.init_and_first_turn("let\'s chat")
        _, _, _ = self.process_utterance("yes")
        _, current_state, _ = self.process_utterance(user_utterance)
        self.assertEqual(current_state['selected_response_rg'], 'CLOSING_CONFIRMATION')
    
    def test_pos_confirmation(self):
        """Check that conversation ends if user positively confirms exiting"""
        self.reset_ask_to_post_launch_sequence()
        alexa_response, _, _ = self.process_utterance("yes")
        self.assertTrue(alexa_response['response']['shouldEndSession'])
    
    def test_neg_confirmation(self):
        """Check that conversation continues and closing confirmation responds if user negatively confirms exiting"""
        self.reset_ask_to_post_launch_sequence()
        alexa_response, current_state, _ = self.process_utterance("no")
        self.assertFalse(alexa_response['response']['shouldEndSession'])
        self.assertEqual(current_state['selected_response_rg'], 'CLOSING_CONFIRMATION')

    def test_neither_response(self):
        """Check that another RG takes over if user does not give a positive or negative answer"""
        self.reset_ask_to_post_launch_sequence()
        alexa_response, current_state, _ = self.process_utterance("what's your favorite color")
        self.assertFalse(alexa_response['response']['shouldEndSession'])
        self.assertNotEqual(current_state['selected_response_rg'], 'CLOSING_CONFIRMATION')

    def test_input_none(self):
        """"Check that inputting None does not result in error"""
        alexa_response, current_state, _ = self.init_and_first_turn('')
        self.assertIn('CLOSING_CONFIRMATION', current_state['response_results'].keys())
    
    @parameterized.expand(['shut up you stupid bot', 'i do not want to chat', 'exit social mode', 'stop talking to me'])
    def test_regex_trigges(self, user_utterance):
        """Check that closing confirmation is triggered by moderate precision regexes"""
        _, _, _ = self.init_and_first_turn("let\'s chat")
        _, _, _ = self.process_utterance("yes")
        _, current_state, _ = self.process_utterance(user_utterance)
        self.assertEqual(current_state['selected_response_rg'], 'CLOSING_CONFIRMATION')


