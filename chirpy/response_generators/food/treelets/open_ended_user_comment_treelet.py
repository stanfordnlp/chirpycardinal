import logging
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.response_generators.food.regex_templates import DoubtfulTemplate
from chirpy.core.response_generator_datatypes import PromptType, ResponseGeneratorResult, PromptResult, AnswerType
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.response_generator import Treelet
from chirpy.core.util import infl
from chirpy.response_generators.food.food_helpers import *
from chirpy.response_generators.food.state import State, ConditionalState

logger = logging.getLogger('chirpylogger')

class OpenEndedUserCommentTreelet(Treelet):
    name = "open_ended_user_comment"

    def classify_user_response(self):
        assert False, "This should never be called."

    def get_prompt(self, conditional_state=None):
        state, utterance, response_types = self.get_state_utterance_response_types()
        cur_entity = self.get_current_entity()

        if conditional_state and conditional_state.cur_food:
            entity = conditional_state.cur_food
        else:
            entity = state.cur_food
            conditional_state = ConditionalState(cur_food=entity)

        if entity is None: return self.emptyPrompt()

        best_attribute, best_attribute_value = get_attribute(entity.name)
        pronoun = infl('them', entity.is_plural)
        if best_attribute: text = 'What do you think?'
        else: text = f'What do you like best about {pronoun}?'
        return PromptResult(text, PromptType.CONTEXTUAL, state=state, cur_entity=entity, conditional_state=conditional_state)

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """ Returns the response. """
        state, utterance, response_types = self.get_state_utterance_response_types()
        # entity = self.get_current_entity()
        entity = state.cur_food
        cur_food = entity.name

        cur_talkable_food = entity.talkable_name

        # if question, sample an unconditional response; if statement, just agree
        if ResponseType.QUESTION in response_types:
            prefix = ''
        elif len(utterance.split()) < 2:
            prefix = ''
        else:
            prefix = f'yeah, i think {cur_talkable_food}'

        neural_response = self.get_neural_response(prefix=prefix)

        # Can we continue the conversation with a factoid?
        if get_factoid(entity) is not None:
            prompt_treelet = self.rg.factoid_treelet.name
            needs_prompt = False
            text = f"{neural_response}"
            cur_entity = entity
        else:
            prompt_treelet = ''
            needs_prompt = True
            concluding_statement = get_concluding_statement(cur_talkable_food)
            text = f"{neural_response} {concluding_statement}"
            cur_entity = None

        return ResponseGeneratorResult(text=text, priority=ResponsePriority.STRONG_CONTINUE,
                                       needs_prompt=needs_prompt, state=state,
                                       cur_entity=cur_entity,
                                       conditional_state=ConditionalState(
                                           prev_treelet_str=self.name,
                                           prompt_treelet=prompt_treelet,
                                           cur_food=None)
                                       )
