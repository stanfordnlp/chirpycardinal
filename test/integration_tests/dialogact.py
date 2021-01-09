from parameterized import parameterized
from .integration_base import BaseIntegrationTest
from agent.agents.agent import apology_string

class TestDialogAct(BaseIntegrationTest):
    launch_sequence = ['let\'s chat']
    
    #def test_dialog_act(self):
    #    """Check that the dialog act classifier output matches the expected value"""
    #    _, current_state, _ = self.process_utterance("diana")
    #    _, current_state, response_text = self.process_utterance("i don't want to talk right now")
    #    self.assertEqual(current_state['dialog_act']['top_1'], 'closing')
    #    self.assertNotIn(apology_string, response_text) # check it didn't result in fatal error
    
    def test_yes_regex(self):
        """Check that is_yes_answer is correctly set when utterance matches YES template"""
        _, current_state, _ = self.process_utterance("yes")
        self.assertEqual(current_state['dialog_act']['is_yes_answer'], True)
    
    def test_no_regex(self):
        """Check that is_no_answer is correctly set when utterance matches NO template"""
        self.reset_ask_to_post_launch_sequence()
        _, current_state, _ = self.process_utterance("no")
        self.assertEqual(current_state['dialog_act']['is_no_answer'], True)

    
    def test_yes_da(self):
        """Check that is_yes_answer is correctly set when utterance does not match YES template but is classified
        by dialog act classifier as pos_ans with high probability"""
        # NOTE: when the bot launches, it asks a yes-no question (would you tell me your name), providing context for 
        # is_yes_answer/is_no_answer classification since the classification uses both bot's and user's utterances
        self.reset_ask_to_post_launch_sequence()
        _, current_state, _ = self.process_utterance("for sure")
        self.assertEqual(current_state['dialog_act']['is_yes_answer'], True)
    
    def test_no_da(self):
        """Check that is_no_answer is correctly set when utterance does not match NO template but is classified
        by dialog act classifier as neg_ans with high probability"""
        # NOTE: when the bot launches, it asks a yes-no question (would you tell me your name), providing context for 
        # is_yes_answer/is_no_answer classification since the classification uses both bot's and user's utterances
        self.reset_ask_to_post_launch_sequence()
        _, current_state, _ = self.process_utterance("not really")
        self.assertEqual(current_state['dialog_act']['is_no_answer'], True)


    
    

    



        
