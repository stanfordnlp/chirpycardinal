from .integration_base import BaseIntegrationTest
from parameterized import parameterized

class TestNavIntent(BaseIntegrationTest):

    @parameterized.expand([
        ("let's talk about giraffes", True),
        ('can we talk about giraffes', True),
        ("let's discuss giraffes", False),
        ("chat giraffes", False),
    ])
    def test_posnav_topic(self, user_utterance, about_keyword):
        _, current_state, response_text = self.init_and_first_turn(user_utterance)
        self.assertTrue(current_state['navigational_intent'].pos_intent)
        self.assertTrue(current_state['navigational_intent'].pos_topic_is_supplied)
        self.assertEqual(current_state['navigational_intent'].pos_topic[0], 'giraffes')
        self.assertEqual(current_state['navigational_intent'].pos_topic[1], about_keyword)

    @parameterized.expand([
        ("i don't want to talk about giraffes", True),
        ("stop talking about giraffes", True),
        ("stop discussing giraffes", False),
        ("i don't want to chat giraffes", False),
    ])
    def test_negnav_topic(self, user_utterance, about_keyword):
        _, current_state, response_text = self.init_and_first_turn(user_utterance)
        self.assertTrue(current_state['navigational_intent'].neg_intent)
        self.assertTrue(current_state['navigational_intent'].neg_topic_is_supplied)
        self.assertEqual(current_state['navigational_intent'].neg_topic[0], 'giraffes')
        self.assertEqual(current_state['navigational_intent'].neg_topic[1], about_keyword)

    @parameterized.expand(["let's chat"])
    def test_posnav_no_topic(self, user_utterance):
        _, current_state, response_text = self.init_and_first_turn(user_utterance)
        self.assertTrue(current_state['navigational_intent'].pos_intent)
        self.assertIsNone(current_state['navigational_intent'].pos_topic)

    @parameterized.expand(["i don't want to talk"])
    def test_negnav_no_topic(self, user_utterance):
        _, current_state, response_text = self.init_and_first_turn(user_utterance)
        self.assertTrue(current_state['navigational_intent'].neg_intent)
        self.assertIsNone(current_state['navigational_intent'].neg_topic)

    @parameterized.expand(["can we talk about"])
    def test_posnav_hesitate(self, user_utterance):
        _, current_state, response_text = self.init_and_first_turn(user_utterance)
        self.assertTrue(current_state['navigational_intent'].pos_intent)
        self.assertTrue(current_state['navigational_intent'].pos_topic_is_hesitate)

    @parameterized.expand(["stop talking about"])
    def test_negnav_hesitate(self, user_utterance):
        _, current_state, response_text = self.init_and_first_turn(user_utterance)
        self.assertTrue(current_state['navigational_intent'].neg_intent)
        self.assertTrue(current_state['navigational_intent'].neg_topic_is_hesitate)

    @parameterized.expand(["let's discuss it"])
    def test_posnav_cur_topic(self, user_utterance):
        _, current_state, response_text = self.init_and_first_turn(user_utterance)
        self.assertTrue(current_state['navigational_intent'].pos_intent)
        self.assertTrue(current_state['navigational_intent'].pos_topic_is_current_topic)

    @parameterized.expand(["i don't want to talk about this", 'change the subject', "let's talk about something else"])
    def test_negnav_cur_topic(self, user_utterance):
        _, current_state, response_text = self.init_and_first_turn(user_utterance)
        self.assertTrue(current_state['navigational_intent'].neg_intent)
        self.assertTrue(current_state['navigational_intent'].neg_topic_is_current_topic)

    @parameterized.expand([
        ("i don't want to talk about giraffes can we talk about zebras", 'giraffes', 'zebras'),
        ("i'd love to talk about zebras stop talking about giraffes", 'giraffes', 'zebras'),
    ])
    def test_negposnav(self, user_utterance, neg_topic, pos_topic):
        _, current_state, response_text = self.init_and_first_turn(user_utterance)
        self.assertTrue(current_state['navigational_intent'].pos_intent)
        self.assertTrue(current_state['navigational_intent'].pos_topic_is_supplied)
        self.assertEqual(current_state['navigational_intent'].pos_topic[0], pos_topic)
        self.assertTrue(current_state['navigational_intent'].neg_intent)
        self.assertTrue(current_state['navigational_intent'].neg_topic_is_supplied)
        self.assertEqual(current_state['navigational_intent'].neg_topic[0], neg_topic)

    # This currently fails; need to fix
    # @parameterized.expand(["i'm talking to my friends"])
    # def test_no_nav_intent(self, user_utterance):
    #     _, current_state, response_text = self.init_and_first_turn(user_utterance)
    #     self.assertFalse(current_state['navigational_intent'].pos_intent)
    #     self.assertFalse(current_state['navigational_intent'].neg_intent)