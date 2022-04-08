from typing import Tuple
from .integration_base import BaseIntegrationTest
from chirpy.core.test_args import TestArgs
import logging
logging.getLogger("asyncio").setLevel(logging.ERROR)
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult
from chirpy.response_generators.wiki.dtypes import State

def get_wiki_info(current_state : dict) -> Tuple[ResponseGeneratorResult, State]:
    return current_state['response_results']['WIKI'], current_state['response_generator_states']['WIKI'],

class TestWikiBaseClass(BaseIntegrationTest):
    launch_sequence = ['let\'s chat', 'my name is judy']
    def process_utterance(self, utterance, test_args=None):
        _, current_state, response_text = super().process_utterance(utterance, test_args)
        response_result, state = get_wiki_info(current_state)
        return response_result, state, response_text

class TestWikiWithCategories(TestWikiBaseClass):
    wiki_test_args = TestArgs(selected_prompt_rg="Categories")
    #Fixme: test entity extraction and then follow up
class TestWikiOpenQuestions(TestWikiBaseClass):
    entity_name = 'Ariana Grande'
    launch_sequence = ['let\'s chat', 'my name is judy', 'i want to talk about ariana grande', 'i like her song love me harder', 'her vocal range']

class TestWikiIntroduceUserMentionedEntity(BaseIntegrationTest):
    def process_utterance(self, utterance, test_args=None):
        _, current_state, response_text = super().process_utterance(utterance, test_args)
        response_result, state = get_wiki_info(current_state)
        return (response_result, current_state['selected_response_rg'], current_state['selected_prompt_rg']) , state, response_text

    launch_sequence = ['let\'s chat', 'my name is judy', 'i want to talk about mickey mouse and minnie mouse', 'no']
    wiki_test_args = TestArgs(selected_prompt_rg="WIKI")
    def test_can_start(self):
        (response_result, selected_response_rg, selected_prompt_rg), state, response_text  = self.process_utterance('let\'s talk about something else', test_args=self.wiki_test_args)
        self.assertIn('WIKI', [selected_response_rg, selected_prompt_rg])
        self.assertEqual(state.prompt_handler, 'Introduce Entity Treelet (WIKI)')
        (response_result, _, _), state, response_text = self.process_utterance('yes', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(response_result.cur_entity.name, 'Minnie Mouse')

    def test_no_start(self):
        (response_result, selected_response_rg, selected_prompt_rg), state, response_text,  = self.process_utterance('let\'s talk about something else', test_args=self.wiki_test_args)
        self.assertIn('WIKI', [selected_response_rg, selected_prompt_rg])
        self.assertEqual(state.prompt_handler, 'Introduce Entity Treelet (WIKI)')
        (response_result, _, _), state, response_text = self.process_utterance('no', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertTrue(state.entity_state['Minnie Mouse'].finished_talking)

class TestTil(TestWikiBaseClass):
    launch_sequence = ['let\'s chat', 'my name is judy', 'i want to talk about abraham lincoln', 'i think his policies were great', 'he left a long lasting legacy']
    def test_double_TIL_prompt_response_then_stop(self):
        #Note: This test will fail if there are less than two TILs for an entity.
        # This can happen if we earlier had multiple entries
        response_result, state, response_text= self.process_utterance('yes', TestArgs(experiment_values={'convpara': False}))
        #First TIL response
        # Sometimes convpara fails and isn't able to continue (STRONG_CONTINUE) hence it does a CAN_START without convpara
        self.assertIn(response_result.priority, [ResponsePriority.STRONG_CONTINUE, ResponsePriority.CAN_START])
        self.assertIn(state.responding_treelet, ["TIL Treelet (WIKI)", "ConvPara TIL Treelet (WIKI)"])
        if state.responding_treelet == "TIL Treelet (WIKI)":
            response_result, state, response_text= self.process_utterance('yes', TestArgs(experiment_values={'convpara': False}))
        else:
            response_result, state, response_text = self.process_utterance("wow that's cool", TestArgs(experiment_values={'convpara': False}))
        #Second TIL response
        self.assertIn(response_result.priority, [ResponsePriority.STRONG_CONTINUE, ResponsePriority.CAN_START])
        self.assertIn(state.responding_treelet, ["TIL Treelet (WIKI)", "ConvPara TIL Treelet (WIKI)"])

    def test_no_to_til_prompt(self):
        # TIL about abraham lincoln
        response_result, state, response_text = self.process_utterance('no not right now i don\'t wanna learn more about that')
        # Ok, no problem. Some other RGs prompt
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertTrue(response_result.needs_prompt)
        self.assertIn('Ok', response_text)

    def test_change_entity_after_til(self):
        response_result, state, response_text = self.process_utterance('yes')
        response_result, state, response_text = self.process_utterance('can we talk about j k rowling')
        self.assertEqual(response_result.cur_entity.name, 'J. K. Rowling')
        self.assertEqual(response_result.priority, ResponsePriority.CAN_START)


class TestWikiSectionNavigation(TestWikiBaseClass):
    entity_name = 'Barack Obama'
    # garbled garbled so that the song's entity page isn't chosen
    launch_sequence = ['let\'s chat', 'my name is judy', 'i want to talk about barack obama', 'i like his stance garbled garbled', 'how he gracefully transitioned power']
    wiki_test_args = TestArgs(selected_prompt_rg="WIKI")
    def test_yes(self):
        response_result, state, response_text= self.process_utterance('yes', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(state.prompt_handler, 'Handle Section Treelet (WIKI)')
        self.assertTrue(state.prompted_options)
        self.assertTrue(state.entity_state[self.entity_name].last_discussed_section)
        self.assertIn(state.entity_state[self.entity_name].last_discussed_section.es_id, set([s.es_id for s in state.entity_state[self.entity_name].suggested_sections]))


    def test_no(self):
        response_result, state, response_text= self.process_utterance('no', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.WEAK_CONTINUE)

    def test_yes_but_another_section(self):
        response_result, state, response_text = self.process_utterance('yes, tell me about his education', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(state.prompt_handler, 'Handle Section Treelet (WIKI)')
        self.assertTrue(any(s.title == 'Education' for s in state.entity_state[self.entity_name].discussed_sections))
        self.assertTrue(state.prompted_options)

    def test_no_but_another_section(self):
        response_result, state, response_text = self.process_utterance('no, tell me about his education', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)

    def test_just_another_section(self):
        response_result, state, response_text = self.process_utterance('tell me about his education', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(state.prompt_handler, 'Handle Section Treelet (WIKI)')
        self.assertTrue(any(s.title == 'Education' for s in state.entity_state[self.entity_name].discussed_sections))
        self.assertTrue(state.prompted_options)

    def test_entity_change(self):
        response_result, state, response_text = self.process_utterance('i love david blaine', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.CAN_START)
        self.assertEqual(response_result.cur_entity.name, 'David Blaine')

    def test_gibberish(self):
        response_result, state, response_text= self.process_utterance('yes', test_args=self.wiki_test_args)
        response_result, state, response_text = self.process_utterance('blithe sesctum', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertTrue(response_result.needs_prompt)

    def test_other_related_phrase(self):
        response_result, state, response_text = self.process_utterance('his charisma', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(state.responding_treelet, 'Open Question Treelet (WIKI)')


class TestWikiResponseGenerator(TestWikiBaseClass):
    launch_sequence = ['let\'s chat', 'my name is judy']
    wiki_test_args = TestArgs(selected_prompt_rg="WIKI")

    # Needs an entity that has less pageviews
    #def test_overview_can_start_on_question(self):
    #    response_result, state, response_text= self.process_utterance('who is camila cabello', test_args=self.wiki_test_args)
    #    self.assertEqual(response_result.priority, ResponsePriority.CAN_START)
    #    self.assertIn('Karla Camila Cabello Estrabao is a Cuban-American singer, songwriter and actress', response_result.text)

    #def test_overview_doesnt_start_on_mention(self):
    #    response_result, state, response_text= self.process_utterance('camila cabello', test_args=self.wiki_test_args)
    #    self.assertEqual(response_result.priority, ResponsePriority.NO)

    def test_overview_cant_start(self):
        """Check that when the user asks to talk about something unlinkable, WIKI does not start"""
        response_result, state, response_text= self.process_utterance('tell me about kajwfwb wahvuehaf', test_args=self.wiki_test_args)
        self.assertEqual(response_result.priority, ResponsePriority.NO)

    def test_can_start_with_open_questions(self):
        response_result, state, response_text = self.process_utterance('can we talk about barack obama')
        self.assertEqual(response_result.priority, ResponsePriority.CAN_START)
        self.assertEqual(state.prompt_handler, 'Open Question Treelet (WIKI)')

    def test_2nd_level_section(self):
        response_result, state, response_text = self.process_utterance('can we talk about chinese new year')

        # Go through two open questions first
        response_result, state, response_text = self.process_utterance('festivities')

        #Then should be given sections to choose from
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(state.prompt_handler, 'Handle Section Treelet (WIKI)')
        self.assertTrue(state.prompted_options)

        #Pick a first level section
        response_result, state, response_text = self.process_utterance('mythology')
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(state.responding_treelet, 'Handle Section Treelet (WIKI)')
        self.assertEqual(state.prompt_handler, 'Handle Section Treelet (WIKI)')
        self.assertTrue(state.prompted_options)

        #Get prompted a second level section and say yes
        response_result, state, response_text = self.process_utterance('yes')
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertEqual(state.responding_treelet, 'Handle Section Treelet (WIKI)')

    #def test_can_start_single_TIL_prompt_response_then_move(self):
        #response_result, state, response_text = self.process_utterance('tell me about about the denarius')
        #self.assertEqual(response_result.priority, ResponsePriority.CAN_START)
        #self.assertIn('was the standard Roman silver coin from its introduction in the Second Punic War Crawford',
                      #response_text)
        #self.assertEqual(state.prompt_handler, 'Handle Section Treelet (WIKI)')
        #self.assertTrue(state.prompted_options)

    def test_neg_navigation(self):
        response_result, state, response_text = self.process_utterance('can we talk about bill gates')
        response_result, state, response_text = self.process_utterance('change the subject')
        self.assertEqual(response_result.priority, ResponsePriority.STRONG_CONTINUE)
        self.assertTrue(response_result.needs_prompt)
        self.assertIn('Ok', response_text)

    def test_change_entity_after_overview(self):
        response_result, state, response_text = self.process_utterance('can we talk about bill gates')
        self.assertEqual(response_result.cur_entity.name, 'Bill Gates')
        response_result, state, response_text = self.process_utterance('can we talk about taylor swift')
        self.assertEqual(response_result.cur_entity.name, 'Taylor Swift')
        self.assertEqual(response_result.priority, ResponsePriority.CAN_START)


    def test_state_reset(self):
        response_result, state, response_text = self.process_utterance('can we talk about abraham lincoln')
        #trigger offensive user
        response_result, state, response_text = self.process_utterance('fuck')
        self.assertFalse(state.prompted_options)
        self.assertFalse(state.prompt_handler)


