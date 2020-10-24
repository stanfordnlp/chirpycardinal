import unittest
from .integration_base import BaseIntegrationTest
from chirpy.core.test_args import TestArgs
from parameterized import parameterized

class OpinionTest(BaseIntegrationTest):
    def get_state(self, current_state):
        return current_state['response_generator_states']['OPINION']

    def get_last_action(self, current_state):
        return self.get_state(current_state).action_history[-1]

class TestGenericOpinion(OpinionTest):
    """Contains tests that does not depend on the policy"""
    launch_sequence = ['let\'s chat', 'my name is judy']

    def test_detect_phrase(self):
        _, current_state, _ = self.process_utterance("let's talk about cats")
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertEqual(self.get_state(current_state).cur_policy, "TwoTurnAgreePolicy")

    def test_immediate(self):
        self.process_utterance("let's talk about movies")
        self.process_utterance("i like star wars")
        _, current_state, _ = self.process_utterance("change the subject", test_args=TestArgs('OPINION'))
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'star wars')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 4)
        action = self.get_state(current_state).action_history[-1]
        self.assertFalse(action.solicit_opinion)
    
    def test_interruption(self):
        """Verify that when interrupted, opinion is able to basically abandon the previous conversation"""
        _, current_state, _ = self.process_utterance("let's talk about cats")
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertTrue(self.get_state(current_state).action_history[-1].solicit_opinion)
        _, current_state, _ = self.process_utterance("should i invest in bitcoin", test_args=TestArgs(selected_prompt_rg="CATEGORIES"))
        self.assertFalse(self.get_state(current_state).last_turn_prompt)
        self.assertFalse(self.get_state(current_state).last_turn_select)

    def test_all_done(self):
        """Test that when we start talking about an phrase we disable all phrase of the same linked entity"""
        _, current_state, _ = self.process_utterance("let's talk about sleep")
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        for same_phrase in ('waking up early', 'sleep', 'sleeping', 'to sleep', 'waking up', 'waking up early', 'taking naps'):
            self.assertIn(same_phrase, self.get_state(current_state).phrases_done)

class TestPolicyExits(OpinionTest):
    launch_sequence = ['let\'s chat', 'my name is judy', "let's talk about dogs"]

    def test_switch_topic(self):
        self.process_utterance("yes")
        _, current_state, _ = self.process_utterance("i want to talk about taylor swift instead")
        self.assertEqual(self.get_state(current_state).cur_phrase, '')
    
    def test_neutral(self):
        _, current_state, _ = self.process_utterance("i don't have an opinion actually")
        self.assertTrue(self.get_last_action(current_state).exit)

class TestPolicyRecognizeDisinterest(OpinionTest):
    launch_sequence = ['let\'s chat', 'my name is judy', "let's talk about dogs", 'no']

    @parameterized.expand(['no reason', 'i just don\'t', 'i don\'t like it'])
    def test_disinterest(self, utterance):
        _, current_state, _ = self.process_utterance(utterance)
        self.assertTrue(self.get_last_action(current_state).exit)

class GenericPolicyTests(OpinionTest):

    launch_sequence = ['let\'s chat', 'my name is judy']

    @unittest.skip('utility function')
    def get_test_args(self):
        raise NotImplementedError

    @unittest.skip("generic test function")
    def test_already_reason(self):
        _, current_state, _ = self.process_utterance("let's talk about cats", test_args=self.get_test_args())
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertTrue(self.get_state(current_state).action_history[-1].solicit_opinion)
        self.assertIn('cats', self.get_state(current_state).phrases_done)
        _, current_state, _ = self.process_utterance("i like cats because they are so fluffy")
        self.assertEqual(len(self.get_state(current_state).action_history), 2)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 4)
        action = self.get_last_action(current_state)
        self.assertTrue(not action.solicit_reason)

class TestAlwaysAgreePolicy(GenericPolicyTests):

    def get_test_args(self):
        return TestArgs(experiment_values={'opinion_policy': 'AlwaysAgreePolicy'})

    def test_full_rollout(self):
        _, current_state, _ = self.process_utterance("let's talk about cats", test_args=self.get_test_args())
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertTrue(self.get_state(current_state).action_history[-1].solicit_opinion)
        self.assertIn('cats', self.get_state(current_state).phrases_done)
        _, current_state, _ = self.process_utterance("they are actually my favorite")
        self.assertEqual(len(self.get_state(current_state).action_history), 2)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 4)
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_reason)
        _, current_state, _ = self.process_utterance("i like cats because they are fluffy")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.suggest_alternative)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_reason)
        _, current_state, _ = self.process_utterance("i like whatever it is because it is awesome")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.exit)

class TestSoftDisagreeSwitchAgreePolicy(GenericPolicyTests):

    def get_test_args(self):
        return TestArgs(experiment_values={'opinion_policy': 'SoftDisagreeSwitchAgreePolicy'})

    def test_full_rollout(self):
        _, current_state, _ = self.process_utterance("let's talk about cats", test_args=self.get_test_args())
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertTrue(self.get_state(current_state).action_history[-1].solicit_opinion)
        self.assertIn('cats', self.get_state(current_state).phrases_done)
        _, current_state, _ = self.process_utterance("cats are my least favorite animal")
        self.assertEqual(len(self.get_state(current_state).action_history), 2)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 0)
        action = self.get_last_action(current_state)
        self.assertTrue(action.solicit_reason)
        _, current_state, _ = self.process_utterance("i hate cats because they don't love you back")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        _, current_state, _ = self.process_utterance("no")
        action = self.get_last_action(current_state)
        self.assertTrue(action.suggest_alternative)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_reason)
        _, current_state, _ = self.process_utterance("i like whatever it is because it is awesome")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.exit)

class TestOneTurnAgreePolicy(GenericPolicyTests):

    def get_test_args(self):
        return TestArgs(experiment_values={'opinion_policy': 'OneTurnAgreePolicy'})

    @unittest.skip("This policy is no longer active")
    def test_full_rollout(self):
        _, current_state, _ = self.process_utterance("let's talk about cats", test_args=self.get_test_args())
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertTrue(self.get_state(current_state).action_history[-1].solicit_opinion)
        self.assertIn('cats', self.get_state(current_state).phrases_done)
        _, current_state, _ = self.process_utterance("they are actually my favorite")
        self.assertEqual(len(self.get_state(current_state).action_history), 2)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 4)
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_reason)
        _, current_state, _ = self.process_utterance("i like cats because they are fluffy")
        action = self.get_last_action(current_state)
        self.assertTrue(action.exit)


class TestShortSoftDisagreePolicy(GenericPolicyTests):

    def get_test_args(self):
        return TestArgs(experiment_values={'opinion_policy': 'ShortSoftDisagreePolicy'})

    def test_full_rollout(self):
        _, current_state, _ = self.process_utterance("let's talk about cats", test_args=self.get_test_args())
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertTrue(self.get_state(current_state).action_history[-1].solicit_opinion)
        self.assertIn('cats', self.get_state(current_state).phrases_done)
        _, current_state, _ = self.process_utterance("they are actually my favorite")
        self.assertEqual(len(self.get_state(current_state).action_history), 2)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 4)
        action = self.get_last_action(current_state)
        self.assertTrue(action.solicit_reason)
        _, current_state, _ = self.process_utterance("i like cats because they are fluffy")
        action = self.get_last_action(current_state)
        self.assertEqual(action.sentiment, 0)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        _, current_state, _ = self.process_utterance("no")
        action = self.get_last_action(current_state)
        self.assertTrue(action.exit)


class TestDisagreeAgreePolicy(GenericPolicyTests):

    def get_test_args(self):
        return TestArgs(experiment_values={'opinion_policy': 'DisagreeAgreePolicy'})

    @unittest.skip('This policy is no longer used')
    def test_full_rollout(self):
        _, current_state, _ = self.process_utterance("let's talk about social media", test_args=self.get_test_args())
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'social media')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertTrue(self.get_state(current_state).action_history[-1].solicit_opinion)
        self.assertIn('social media', self.get_state(current_state).phrases_done)
        _, current_state, _ = self.process_utterance("social media are my least favorite thing")
        self.assertEqual(len(self.get_state(current_state).action_history), 2)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'social media')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 0)
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_reason)
        self.assertEqual(action.sentiment, 4)
        _, current_state, _ = self.process_utterance("i hate social media because they don't are just the worst")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        self.assertEqual(action.sentiment, 0)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.suggest_alternative)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_reason)
        _, current_state, _ = self.process_utterance("i like whatever it is because it is awesome")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.exit)


class TestDisagreeAgreeSwitchAgreePolicy(GenericPolicyTests):

    def get_test_args(self):
        return TestArgs(experiment_values={'opinion_policy': 'DisagreeAgreeSwitchAgreePolicy'})

    def test_full_rollout(self):
        _, current_state, _ = self.process_utterance("let's talk about social media", test_args=self.get_test_args())
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'social media')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertTrue(self.get_state(current_state).action_history[-1].solicit_opinion)
        self.assertIn('social media', self.get_state(current_state).phrases_done)
        _, current_state, _ = self.process_utterance("social media are my least favorite thing")
        self.assertEqual(len(self.get_state(current_state).action_history), 2)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'social media')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 0)
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_reason)
        self.assertEqual(action.sentiment, 4)
        _, current_state, _ = self.process_utterance("i hate social media because they don't are just the worst")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        self.assertEqual(action.sentiment, 0)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.suggest_alternative)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_reason)
        _, current_state, _ = self.process_utterance("i like whatever it is because it is awesome")
        action = self.get_last_action(current_state)
        self.assertEqual(action.sentiment, 4)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        _, current_state, _ = self.process_utterance("yes")
        action = self.get_last_action(current_state)
        self.assertTrue(action.exit)

class TestTwoTurnAgreePolicy(GenericPolicyTests):

    def get_test_args(self):
        return TestArgs(experiment_values={'opinion_policy': 'TwoTurnAgreePolicy'})

    def test_full_rollout(self):
        _, current_state, _ = self.process_utterance("let's talk about cats", test_args=self.get_test_args())
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)
        self.assertEqual(len(self.get_state(current_state).action_history), 1)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 2)
        self.assertTrue(self.get_state(current_state).action_history[-1].solicit_opinion)
        self.assertIn('cats', self.get_state(current_state).phrases_done)
        _, current_state, _ = self.process_utterance("they are actually my favorite")
        self.assertEqual(len(self.get_state(current_state).action_history), 2)
        self.assertEqual(self.get_state(current_state).cur_phrase, 'cats')
        self.assertEqual(self.get_state(current_state).cur_sentiment, 4)
        action = self.get_last_action(current_state)
        self.assertTrue(action.solicit_reason)
        _, current_state, _ = self.process_utterance("i like cats because they are fluffy")
        action = self.get_last_action(current_state)
        self.assertEqual(action.sentiment, 4)
        self.assertTrue(action.give_agree and action.give_reason and action.solicit_agree)
        _, current_state, _ = self.process_utterance("no")
        action = self.get_last_action(current_state)
        self.assertTrue(action.exit)


class TestContinuation(GenericPolicyTests):

    @unittest.skip("This is no longer true now that we don't ask for continuation")
    def test_continuation(self):
        """ Verify that after a successful run, we ask whether the user wants to continue, and do so """
        _, current_state, _ = self.process_utterance("let's talk about youtube") # type: ignore
        self.assertIn(self.get_state(current_state).cur_policy, ['ShortSoftDisagreePolicy', 'TwoTurnAgreePolicy'])
        self.process_utterance("youtube are actually my favorite")
        self.process_utterance("i like youtube because i like the content")
        _, current_state, _ = self.process_utterance("not really")
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.exit)
        self.assertEqual(self.get_state(current_state).cur_phrase, '') # We no longer evaluate on first episode

        # Restart episode with forced policy
        self.process_utterance("let's talk about cats", test_args=TestAlwaysAgreePolicy.get_test_args(None)) # type: ignore
        self.process_utterance("cats are actually my favorite")
        self.process_utterance("i like cats because cats are fluffy")
        self.process_utterance("yeah definitely")
        self.process_utterance("yes")
        self.process_utterance("i like whatever they are because they are awesome")
        _, current_state, _ = self.process_utterance("yeah definitely")
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.exit)
        _, current_state, _ = self.process_utterance("yes")
        self.assertEqual(self.get_state(current_state).cur_policy, 'OneTurnAgreePolicy')

class TestTypedPrompt(OpinionTest):
    launch_sequence = ['let\'s chat', 'my name is judy']

    def test_typed_prompt(self):
        self.process_utterance("let's talk about cats")
        self.process_utterance("yes i love cats")
        self.process_utterance("change the subject", test_args=TestArgs(selected_prompt_rg='NEURAL_CHAT'))
        _, current_state, _ = self.process_utterance("i love petting cats", test_args=TestArgs(selected_prompt_rg='OPINION'))
        turns_waited = 0
        for i in range(10):
            turns_waited = i
            if current_state['selected_prompt_rg'] == 'OPINION':
                break
            _, current_state, _ = self.process_utterance("i love petting cats", test_args=TestArgs(selected_prompt_rg='OPINION'))
        if turns_waited == 9:
            self.fail("Waited 10 turns but opinion didn't get prompted")
        self.assertEqual(self.get_state(current_state).cur_phrase, 'dogs')

class DoYouLikeForceStart(OpinionTest):
    launch_sequence = ['let\'s chat', 'my name is judy']

    @unittest.skip("Too risky. Opinion should never trigger with FORCE_START")
    def test_force_start(self):
        _, current_state, _ = self.process_utterance("do you like bts")
        action = self.get_state(current_state).action_history[-1]
        self.assertTrue(action.solicit_opinion)