from .integration_base import BaseIntegrationTest
from parameterized import parameterized

class TestEntityTracker(BaseIntegrationTest):
    launch_sequence = ['let\'s chat', 'my name is abi']

    def test_user_no_highprec_ent(self):
        """Check that when the user says an utterance without any high prec entities, cur_entity doesn't change"""
        _, current_state, response_text = self.process_utterance("whatever")
        cur_entity = current_state['entity_tracker'].cur_entity
        _, current_state, response_text = self.process_utterance("okay")
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'], cur_entity)  # check the entity is the same before and after "okay"

    def test_user_highprec_ent(self):
        """Check that when the user says a high precision entity (without posnav intent) we set it as cur_entity"""
        _, current_state, response_text = self.process_utterance('do you like ariana grande')
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, 'Ariana Grande')  # ariana grande

    def test_user_multiple_highprec_ent(self):
        """Check that when the user says multiple high precision entities (without posnav intent), we set one as
        cur_entity and put the others in user_mentioned_untalked"""
        _, current_state, response_text = self.process_utterance('do you prefer ariana grande or taylor swift')
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, 'Taylor Swift')
        self.assertIn('Ariana Grande', [ent.name for ent in current_state['entity_tracker'].user_mentioned_untalked])

    @parameterized.expand(["change the subject", "please can we talk about something else alexa"])
    def test_user_negnav(self, user_utterance):
        """Check that when the user says 'change the subject', we put cur_entity in rejected list and change cur_entity"""
        _, current_state, response_text = self.process_utterance("let's talk about ariana grande")
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, 'Ariana Grande')

        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertTrue(current_state['navigational_intent'].neg_intent)
        self.assertTrue(current_state['navigational_intent'].neg_topic_is_current_topic)
        self.assertIsNone(current_state['entity_tracker'].history[-1]['user'])  # check that the entity tracker set cur_entity to None after the user's utterance
        self.assertIn('Ariana Grande', [ent.name for ent in current_state['entity_tracker'].talked_rejected])

    @parameterized.expand(["i want to talk about werner herzog", "i don't know hey can we discuss werner herzog",
                           "we could just chat about werner herzog", "i'd like to learn about werner herzog"])
    def test_user_posnav(self, user_utterance):
        """
        Check that when the user says PosNav 'i want to talk about X', where X is unrelated to the cur_entity,
        we change cur_entity to X"""

        # First set something else as cur_entity
        _, current_state, response_text = self.process_utterance('let`s talk about ariana grande')
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, 'Ariana Grande')

        # Then give posnav towards werner herzog
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertTrue(current_state['navigational_intent'].pos_intent)
        self.assertEqual(current_state['navigational_intent'].pos_topic[0], 'werner herzog')
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, 'Werner Herzog')  # cur entity is Werner Herzog after processing user utterance

    @parameterized.expand(["i don't want to talk about lizards let's talk about giraffes", "can we talk about giraffes i don't wanna talk about lizards"])
    def test_user_negposnav(self, user_utterance):
        """Check that when the user says PosNav+NegNav 'i don't want to talk about X, let's discuss Y', we reject X and make Y the cur_entity"""
        _, current_state, response_text = self.process_utterance(user_utterance)
        self.assertTrue(current_state['navigational_intent'].pos_intent)
        self.assertEqual(current_state['navigational_intent'].pos_topic[0], 'giraffes')
        self.assertTrue(current_state['navigational_intent'].neg_intent)
        self.assertEqual(current_state['navigational_intent'].neg_topic[0], 'lizards')
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, 'Giraffe')  # cur entity is giraffe
        self.assertIn('Lizard', [ent.name for ent in current_state['entity_tracker'].talked_rejected])  # lizard is in rejected

    def test_user_newtopic(self):
        """Check that when the user moves onto a new topic (without indicating NegNav towards current topic or PosNav
        towards new topic), we put cur_entity on finished list and change cur_entity"""
        # First set something else as cur_entity
        _, current_state, response_text = self.process_utterance('do you like ariana grande')
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, 'Ariana Grande')  # check that entity linker made ariana grande the cur_entity after the user's utt

        # Then mention a new high prec entity
        _, current_state, response_text = self.process_utterance('i also like werner herzog')
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, 'Werner Herzog')  # check that entity linker made werner herzog the cur_entity after the user's utt
        self.assertIn('Ariana Grande', [ent.name for ent in current_state['entity_tracker'].talked_finished])

    def test_rg_newtopic(self):
        """Check that when a RG provides a new entity, we save it as cur_entity, and if it provides an expected_type,
        we save that, and use it to find the right user utterance on the next turn"""
        _, current_state, response_text = self.process_utterance("let's talk about travel")
        self.assertEqual(current_state['selected_response_rg'], 'CATEGORIES')
        categories_result = current_state['response_results']['CATEGORIES']
        self.assertEqual(current_state['entity_tracker'].cur_entity, categories_result.cur_entity)
        self.assertEqual(current_state['entity_tracker'].expected_type, categories_result.expected_type)

        _, current_state, response_text = self.process_utterance("my favorite place is the isle of skye")
        self.assertEqual(current_state['entity_tracker'].history[-1]['user'].name, 'Isle of Skye')



