from .integration_base import BaseIntegrationTest
from chirpy.core.test_args import TestArgs


class TestCoronavirusResponseGenerator(BaseIntegrationTest):
    launch_sequence = ['let\'s chat', 'my name is test']
    # The tests fail when the offensive classifier flags the response from News RG.

    def get_coronavirus_state(self, current_state: dict):
        return current_state['response_generator_states']['CORONAVIRUS']

    def assert_triggers_comforting_phrase(self, news_state, response_text):
        self.assertTrue(bool(news_state.last_wapo_thread))
        self.assertIn('Here\'s a story about', response_text)
        self.assertIn('Do you want to know more?', response_text)
        self.assert_know_more_treelet(news_state)

    def test_triggers_comforting_phrase(self):
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("comforting_phrase", self.get_coronavirus_state(current_state).used_treelets_str)

    def test_only_triggers_comforting_phrase_once(self):
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("comforting_phrase", self.get_coronavirus_state(current_state).used_treelets_str)
        _, current_state, response_text = self.process_utterance('coronavirus')
        comforting_phrase_counts = self.get_coronavirus_state(current_state).used_treelets_str.count("comforting_phrase")
        self.assertEqual(comforting_phrase_counts, 1)

    def test_goes_to_news_after_comforting_phrase(self):
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("comforting_phrase", self.get_coronavirus_state(current_state).used_treelets_str)
        _, current_state, response_text = self.process_utterance('yes')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("coronavirus_news", self.get_coronavirus_state(current_state).used_treelets_str)

    def test_does_not_go_to_news_after_comforting_phrase(self):
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("comforting_phrase", self.get_coronavirus_state(current_state).used_treelets_str)
        _, current_state, response_text = self.process_utterance('no')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertNotEqual("coronavirus_news", self.get_coronavirus_state(current_state).cur_treelet_str)

    def test_triggers_news(self):
        _, current_state, response_text = self.process_utterance('coronavirus news')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("coronavirus_news", self.get_coronavirus_state(current_state).used_treelets_str)

    def test_get_to_neural_after_comforting_phrase(self):
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("comforting_phrase", self.get_coronavirus_state(current_state).used_treelets_str)
        _, current_state, response_text = self.process_utterance('let\'s talk about something else')
        _, current_state, response_text = self.process_utterance('yes')
        self.assertNotEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("neural_generation", self.get_coronavirus_state(current_state).used_treelets_str)

    def test_get_to_neural_after_rejecting_news(self):
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("comforting_phrase", self.get_coronavirus_state(current_state).used_treelets_str)
        _, current_state, response_text = self.process_utterance('no')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("I know this situation has been very stressful for many people", response_text)
        self.assertEqual("neural_generation", self.get_coronavirus_state(current_state).cur_treelet_str)

    def test_get_to_neural_in_middle_of_news(self):
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("comforting_phrase", self.get_coronavirus_state(current_state).used_treelets_str)
        _, current_state, response_text = self.process_utterance('ok')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        _, current_state, response_text = self.process_utterance('no')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("I know this situation has been very stressful for many people", response_text)
        self.assertEqual("neural_generation", self.get_coronavirus_state(current_state).cur_treelet_str)

    def test_get_to_neural_after_all_news(self):
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("comforting_phrase", self.get_coronavirus_state(current_state).used_treelets_str)
        _, current_state, response_text = self.process_utterance('ok')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        _, current_state, response_text = self.process_utterance('ok')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        _, current_state, response_text = self.process_utterance('ok')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        _, current_state, response_text = self.process_utterance('ok')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        _, current_state, response_text = self.process_utterance('ok')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("neural_generation", self.get_coronavirus_state(current_state).used_treelets_str)

    def test_give_a_smooth_transition_after_negative_navigational_intent(self):
        _, current_state, response_text = self.process_utterance('coronavirus')
        self.assertEqual(current_state['selected_response_rg'], 'CORONAVIRUS')
        self.assertIn("comforting_phrase", self.get_coronavirus_state(current_state).used_treelets_str)
        _, current_state, response_text = self.process_utterance('let\'s talk about something else')
        self.assertIn("I've heard that a ton of people are watching movies while they shelter in place.", response_text)
        self.assertTrue(current_state['response_generator_states']['MOVIES'].last_turn_was_prompt)
        self.assertTrue(current_state['response_generator_states']['MOVIES'].last_turn_was_movies)