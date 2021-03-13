from .integration_base import BaseIntegrationTest
from agents.local_agent import apology_string

class TestQuestion(BaseIntegrationTest):
    launch_sequence = ['let\'s chat']
    
    def test_is_question(self):
        """Check that the question classifier predicts True for question"""
        self.reset_ask_to_post_launch_sequence()
        _, current_state, response_text = self.process_utterance("my day was good how was yours")
        self.assertEqual(current_state['question']['is_question'], True)
        self.assertNotIn(apology_string, response_text) # check it didn't result in fatal error

    def test_not_question(self):
        """Check that the question classifier predicts False for utterance that is not question"""
        self.reset_ask_to_post_launch_sequence()
        _, current_state, response_text = self.process_utterance("I like dogs")
        self.assertEqual(current_state['question']['is_question'], False)
        self.assertNotIn(apology_string, response_text) # check it didn't result in fatal error
    
    

    



        
