from .integration_base import BaseIntegrationTest
from parameterized import parameterized

class TestRedQuestionResponseGenerator(BaseIntegrationTest):
    launch_sequence = ['let\'s chat']
    @parameterized.expand(['what\'s your name', 'what are you called'])
    def test_askname(self, user_utterance):
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertIn('Sorry, I have to remain anonymous for this competition.', response_text)

    @parameterized.expand(['who are you', 'what are you'])
    def test_askidentity(self, user_utterance):
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertIn('I am an Alexa Prize social bot built by a university.', response_text)

    @parameterized.expand(['who are you voting for', 'what are you talking about'])
    def test_askpersonal(self, user_utterance):
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertNotIn('I am an Alexa Prize social bot built by a university.', response_text)

    @parameterized.expand(['where are you', 'where are you from', 'where do you live'])
    #@parameterized.expand(['where are you', 'where are you from', 'where do you live', 'where are your favorite countries'])
    def test_asklocation(self, user_utterance):
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertIn('I live in the cloud.', response_text)

    @parameterized.expand(['siri', 'cortana'])
    def test_siri(self, assistant):
        _, current_state, response_text = self.process_utterance(f'do you like {assistant}')
        self.assertIn(f'I don\'t know much about {assistant}', response_text)

    @parameterized.expand(['should i sue my landlord'])
    def test_legal(self, user_utterance):
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertIn('I\'m unable to offer legal advice.', response_text)

    @parameterized.expand(['should i get laser eye surgery'])
    def test_medical(self, user_utterance):
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertIn('I\'m unable to offer medical advice.', response_text)

    @parameterized.expand(['do i need a 401k'])
    def test_financial(self, user_utterance):
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertIn('I\'m unable to offer financial advice.', response_text)

    @parameterized.expand(['with me getting in trouble', 'just hanging out with my grandma'])
    def test_no_longer_trigger(self, user_utterance):
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertNotEqual(current_state['selected_response_rg'], 'RED_QUESTION')


