import random
import logging
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.response_generators.food.regex_templates import DoubtfulTemplate
from chirpy.core.response_generator_datatypes import PromptType, ResponseGeneratorResult, PromptResult, AnswerType
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.response_generator import Treelet
from chirpy.response_generators.food.food_helpers import *
from chirpy.response_generators.food.state import State, ConditionalState
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW

logger = logging.getLogger('chirpylogger')

class FactoidTreelet(Treelet):
    name = "food_factoid_treelet"

    def classify_user_response(self):
        assert False, "This should never be called."

    def get_prompt(self, conditional_state=None):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if conditional_state and conditional_state.cur_food:
            cur_food = conditional_state.cur_food
        else:
            cur_food = state.cur_food
            conditional_state = ConditionalState(cur_food=cur_food)
        entity = self.rg.state_manager.current_state.entity_tracker.cur_entity
        return PromptResult(text=get_factoid(cur_food), prompt_type=PromptType.CONTEXTUAL,
                            state=state, cur_entity=entity, conditional_state=conditional_state, answer_type=AnswerType.QUESTION_SELFHANDLING)

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """ Returns the response. """
        state, utterance, response_types = self.get_state_utterance_response_types()
        cur_entity = state.cur_food
        cur_food = cur_entity.name
        cur_talkable_food = cur_entity.talkable_name

        # We respond to factoids with a neural generation.
        if ResponseType.THATS in response_types:
            response = random.choice(RESPONSE_TO_THATS)
        elif ResponseType.DIDNT_KNOW in response_types:
            response = random.choice(RESPONSE_TO_DIDNT_KNOW)
        else:
            response = self.rg.get_neural_response(prefix=None, conditions=[lambda response: 'agree' in response])
        conclusion = get_concluding_statement(cur_talkable_food)
        text = f"{response} {conclusion}"
        return ResponseGeneratorResult(text=text, priority=priority,
                                       needs_prompt=True, state=state,
                                       cur_entity=None,
                                       conditional_state=ConditionalState(
                                           prev_treelet_str=self.name,
                                           cur_food=cur_food
                                       ))
