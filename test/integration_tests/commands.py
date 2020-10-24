from .integration_base import BaseIntegrationTest

class TestCommandsResponseGenerator(BaseIntegrationTest):
    launch_sequence = ['let\'s chat', 'my name is jamie']

    def test_command_after_firstutt(self):
        _, current_state, response_text = self.init_and_first_turn()
        _, current_state, response_text = self.process_utterance('play music')
        self.assertIn('This is an Alexa Prize Socialbot. I\'m happy to chat with you', response_text)

    def test_command_after_introseq(self):
        _, current_state, response_text = self.process_utterance('play music')
        self.assertIn('This is an Alexa Prize Socialbot. I\'m happy to chat with you', response_text)