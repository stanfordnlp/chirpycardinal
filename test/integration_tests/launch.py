from .integration_base import BaseIntegrationTest
from parameterized import parameterized


class TestLaunchSequence(BaseIntegrationTest):
    """These tests are for the launch sequence UX, which includes RGs other than LAUNCH"""

    def get_neuralchat_state(self, current_state):
        """Returns the RG state for the NEURAL_CHAT RG"""
        return current_state['response_generator_states']['NEURAL_CHAT']

    def get_neuralchat_response(self, current_state):
        return current_state['response_results']['NEURAL_CHAT']

    @parameterized.expand(["", "let's chat", "let's talk about cats", "fuck let's chat", "let\'s chat alexa are you better than siri"])
    def test_launchphrase(self, launch_phrase):
        """
        Check that we always open with 'Hi, this is an Alexa Prize Socialbot', even if the launch utterance is empty,
        contains a topic, an offensive phrase, or a red question.
        """
        _, current_state, response_text = self.init_and_first_turn(launch_phrase)
        self.assertIn("Hi, this is an Alexa Prize Socialbot", response_text)

    def test_user_says_no_to_name(self):
        _, current_state, response_text = self.init_and_first_turn()
        self.assertIn("Is it all right if I ask for your name?", response_text)
        _, current_state, response_text = self.process_utterance('no')
        self.assertIn('Let\'s move on!', response_text)

    def test_user_says_yes_to_name(self):
        _, current_state, response_text = self.init_and_first_turn()
        self.assertIn("Is it all right if I ask for your name?", response_text)
        _, current_state, response_text = self.process_utterance('ok')
        self.assertIn('Ok, great! What\'s your name?', response_text)
        _, current_state, response_text = self.process_utterance('simon')
        self.assertIn('to meet you, simon!', response_text)

    def test_user_gives_name_in_phrase(self):
        _, current_state, response_text = self.init_and_first_turn()
        self.assertIn("Is it all right if I ask for your name?", response_text)
        _, current_state, response_text = self.process_utterance('yeah my name is simon blah')
        self.assertIn('to meet you, simon!', response_text)

    def test_user_gives_name_in_yes_phrase(self):
        _, current_state, response_text = self.init_and_first_turn()
        self.assertIn("Is it all right if I ask for your name?", response_text)
        _, current_state, response_text = self.process_utterance('yeah simon')
        self.assertIn('to meet you, simon!', response_text)

    def test_greeting(self):
        """Check that we greet the user by their name after they give it"""
        _, current_state, response_text = self.init_and_first_turn()
        self.assertIn("Is it all right if I ask for your name?", response_text)
        _, current_state, response_text = self.process_utterance('my name is jamie')
        self.assertIn('to meet you, jamie!', response_text)

    def test_noname(self):
        """Check that if we can't detect user name, we ask one more time then move on"""
        _, current_state, response_text = self.init_and_first_turn()
        self.assertIn("Is it all right if I ask for your name?", response_text)
        _, current_state, response_text = self.process_utterance("test blah")
        self.assertIn('Would you mind repeating it?', response_text)
        _, current_state, response_text = self.process_utterance("test blah")
        self.assertIn("to meet you!", response_text)

    def test_neuralchat_starts(self):
        """Check that neural chat gives a prompt after we greet the user"""
        _, current_state, response_text = self.init_and_first_turn()
        _, current_state, response_text = self.process_utterance('my name is jamie')
        self.assertEqual(current_state['selected_prompt_rg'], 'NEURAL_CHAT')