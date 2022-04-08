import logging
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT, NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, \
    OPTIONAL_TEXT_MID
from chirpy.core.response_generator_datatypes import PromptType, ResponseGeneratorResult, PromptResult, emptyResult, AnswerType
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.response_generator import Treelet
from chirpy.response_generators.food.food_helpers import *
from chirpy.response_generators.food.state import State, ConditionalState

import inflect
engine = inflect.engine()

logger = logging.getLogger('chirpylogger')


class IntroductoryTreelet(Treelet):
    name = "food_introductory_treelet"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """ Returns the response.
        :param **kwargs:
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        entity = self.rg.get_current_entity()
        if entity is None: return self.emptyResult()
        cur_food = entity.name.lower()
        cur_talkable_food = entity.talkable_name

        logger.primary_info(f"FOOD intro treelet examining {cur_food} ({is_known_food(cur_food)})")

        if not is_known_food(cur_food):
            logger.error("FOOD Intro Treelet was triggered, but current entity is unknown in our database.")
            return self.emptyResult()

        intro = get_intro_acknowledgement(cur_talkable_food, entity.is_plural)

        pronoun = 'they' if entity.is_plural else 'it'
        copula = 'they\'re' if entity.is_plural else 'it\'s'


        # decide on an internal prompt
        if get_custom_question(cur_food) or is_subclassable(cur_food):
            prompt_treelet = self.rg.comment_on_favorite_type_treelet.name
            text = intro
        else:
            best_attribute, best_attribute_value = get_attribute(cur_food)
            custom_comment = get_custom_comment(cur_food)
            if custom_comment is not None:
                text = f"{intro} {custom_comment}"
            elif best_attribute is not None:
                if best_attribute == 'ingredient':
                    attribute_comment = f"Personally, I especially like the {best_attribute_value} in it, I think it gives {pronoun} a really nice flavor."
                elif best_attribute == 'texture':
                    attribute_comment = f"Personally, I love {pronoun} texture, especially how {copula} so {best_attribute_value}."
                text = f"{intro} {attribute_comment}"
            elif is_ingredient(cur_food):
                parent_food = sample_food_containing_ingredient(cur_food)
                containment_response = f"In my opinion, I think {copula} especially good as a part of {engine.a(parent_food)}."
                text = f"{intro} {containment_response}"
            else:
                neural_response = self.get_neural_response(prefix=f'I especially love how {pronoun}')
                text = f"{intro} {neural_response}"
            prompt_treelet = self.rg.open_ended_user_comment_treelet.name

        # special exceptional activation check
        neural_chat_state = self.rg.state_manager.current_state.response_generator_states.get('NEURAL_CHAT', None)
        if neural_chat_state is not None and getattr(neural_chat_state, 'next_treelet', None):
            priority = ResponsePriority.FORCE_START

        return ResponseGeneratorResult(text=text, priority=priority,
                                       needs_prompt=False, state=state,
                                       cur_entity=entity,
                                       conditional_state=ConditionalState(cur_food=entity,
                                                                          prompt_treelet=prompt_treelet))

    def get_prompt(self, **kwargs):
        return None
        # """ Returns the prompt that should be used if this treelet is currently active"""
        # entity = self.rg.state_manager.current_state.entity_tracker.cur_entity
        # cur_food = state.cur_food if state.cur_food else entity.name
        # state.last_turn_was_food = True
        # priority = PromptType.FORCE_START if is_known_food(cur_food) else PromptType.NO
        # logger.primary_info("Getting prompt from intro treelet of food wiki")
        # prompt_text = f"What type of {cur_food} do you like the most?"
        # return PromptResult(prompt_text, priority, state, cur_entity=entity,
        #                         conditional_state=ConditionalState(
        #                             prompt=True,
        #                             cur_treelet_str="get_other_type",
        #                             cur_food=entity.name,
        #                             response=prompt_text))
