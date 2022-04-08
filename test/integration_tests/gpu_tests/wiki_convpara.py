from typing import Tuple
import logging
import unittest

from chirpy.core.test_args import TestArgs
from test.integration_tests.wiki import TestWikiBaseClass

logging.getLogger("asyncio").setLevel(logging.ERROR)
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult
from chirpy.response_generators.wiki.dtypes import State

def get_wiki_info(current_state : dict) -> Tuple[ResponseGeneratorResult, State]:
    return current_state['response_results']['WIKI'], current_state['response_generator_states']['WIKI'],

class TestWikiTilConvparaCanStart(TestWikiBaseClass):
    launch_sequence = ['let\'s chat', 'my name is judy']
    _multiprocess_shared_ = True
    def process_utterance(self, utterance):
        return super().process_utterance(utterance, TestArgs(experiment_values={'convpara': True}))

    def test_convpara_til(self):
        response_result, state, response_text= self.process_utterance('i want to talk about monty python', )
        response_result, state, response_text= self.process_utterance('i like the skits they make me laugh', )
        response_result, state, response_text= self.process_utterance('yes', )
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(state.responding_treelet, 'ConvPara TIL Treelet (WIKI)')
        self.assertEqual(state.prompt_handler, 'ConvPara TIL Treelet (WIKI):paraphrase_handler')
        self.assertEqual(len(state.entity_state['Monty Python'].tils_used), 1)

class TestWikiTilConvparaHandlePrompts(TestWikiBaseClass):
    launch_sequence = ['let\'s chat', 'my name is judy', 'i want to talk about monty python', 'i like the skits they make me laugh', 'yes']
    _multiprocess_shared_ = True

    def process_utterance(self, utterance):
        return super().process_utterance(utterance, TestArgs(experiment_values={'convpara': True}))

    def test_convpara_til_interested(self):
        response_result, state, response_text= self.process_utterance('wow that\'s cool')
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(response_result.conditional_state.responding_treelet, 'ConvPara TIL Treelet (WIKI)')
        if  state.convpara_measurement['codepath'] == 'paraphrase_for_answer_to_did_you_know' :
            response_result, state, response_text = self.process_utterance('wow that\'s cool')
            self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
            self.assertEqual(response_result.conditional_state.responding_treelet, 'ConvPara TIL Treelet (WIKI)')
        self.assertEqual(len(state.entity_state['Monty Python'].tils_used), 2)

    def test_convpara_til_confused(self):
        response_result, state, response_text= self.process_utterance("that doesn't sound right")
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(response_result.conditional_state.responding_treelet, 'ConvPara TIL Treelet (WIKI)')
        self.assertEqual(state.convpara_measurement['codepath'], 'apologize_with_original_phrasing_for_unclear_paraphrase')
        self.assertEqual(len(state.entity_state['Monty Python'].tils_used), 1)

    @unittest.skip('removed functionality')
    def test_convpara_til_why(self):
        response_result, state, response_text= self.process_utterance("why is that")
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(response_result.conditional_state.responding_treelet, 'ConvPara TIL Treelet (WIKI)')
        self.assertIn(state.convpara_measurement['codepath'], ['deflect_question_with_original_phrasing',
                                                                    'paraphrase_for_answer_to_did_you_know'])
        self.assertEqual(len(state.entity_state['Monty Python'].tils_used), 1)

    def test_convpara_til_disinterested(self):
        response_result, state, response_text= self.process_utterance("boring")
        self.assertEqual(response_result.priority, ResponsePriority.WEAK_CONTINUE)
        self.assertEqual(response_result.conditional_state.responding_treelet, 'ConvPara TIL Treelet (WIKI)')
        self.assertEqual(state.convpara_measurement['codepath'], 'apology_handover_for_explicitly_disinterested')
        self.assertEqual(len(state.entity_state['Monty Python'].tils_used), 1)

# This test depends on the amount of content used, which depends on the chosen generation
#    def test_convpara_til_question(self):
#        response_result, state, response_text= self.process_utterance("what do you mean")
#        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
#        self.assertEqual(response_result.conditional_state.responding_treelet, 'ConvPara TIL Treelet (WIKI)')
#        self.assertEqual(state.convpara_measurement['codepath'], 'paraphrase_question_reply')
#        self.assertEqual(len(state.entity_state['Monty Python'].tils_used), 1)
#        response_result, state, response_text= self.process_utterance("what do you mean")
#        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
#        self.assertEqual(response_result.conditional_state.responding_treelet, 'ConvPara TIL Treelet (WIKI)')
#        self.assertEqual(state.convpara_measurement['codepath'], "nonparaphrase_after_2_paraphrases")
#        self.assertEqual(len(state.entity_state['Monty Python'].tils_used), 1)
