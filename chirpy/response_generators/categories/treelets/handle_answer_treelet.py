import logging
from random import choice

from chirpy.annotators.gpt2ed import GPT2ED
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, ResponsePriority, emptyResult
from chirpy.response_generators.categories.classes import Treelet, ConditionalState, State
from chirpy.response_generators.categories.categories import CATEGORYNAME2CLASS
from chirpy.core.regex.templates import DontKnowTemplate, RESPONSE_TO_DONT_KNOW, \
                                        BackChannelingTemplate, RESPONSE_TO_BACK_CHANNELING, \
                                        EverythingTemplate, RESPONSE_TO_EVERYTHING_ANS, \
                                        NotThingTemplate, RESPONSE_TO_NOTHING_ANS, \
                                        WhatAboutYouTemplate, RESPONSE_TO_WHAT_ABOUT_YOU
from chirpy.response_generators.neural_helpers import get_random_fallback_neural_response

logger = logging.getLogger('chirpylogger')

# # If the user said an entity, and no other RGs respond
# ENT_ACKNOWLEDGE = [
#     "Cool!",
#     "Awesome!",
#     "Interesting!",
#     "Sounds good! ",
# ]
#
# # If the user didn't say an entity, e.g. "I don't know"
# NO_ENT_ACKNOWLEDGE = [
#     "Oh ok. No problem! ",
#     "No worries! ",
#     "All right then. ",
#     "Sure thing! ",
# ]


ACKNOWLEDGE_AND_ASK_SECOND_QUESTION = [
    "Oh OK! Speaking of {}, {}",
    "All right then! On the subject of {}, {}",
]



class HandleAnswerTreelet(Treelet):

    def get_response(self, state: State, state_manager) -> ResponseGeneratorResult:
        """
        Handle the user's answer to a categories question on the previous turn.

        If the cur_entity in the entity tracker is still the same category we set at the end of last turn, give a vague
        acknowledgement and ask a followup question. Otherwise, say nothing.
        """

        entity_tracker_state = state_manager.current_state.entity_tracker  # EntityTrackerState
        prev_turn_entity = entity_tracker_state.history[-2]['response']  # the cur_entity at the end of the previous turn e.g. 'Food' or 'Art'
        if 'prompt' in entity_tracker_state.history[-2]:
            prev_turn_entity = entity_tracker_state.history[-2]['prompt']

        # If the cur_entity has changed from the end of the last turn (e.g. because the user indicated they don't want
        # to talk about this category, or because the user named an entity which is now the cur_entity), say nothing.     
        # Additionally, if we have just used prompt from another RG (state.just_asked == True), return an empty prompt so that RG can take over.
        if entity_tracker_state.cur_entity != prev_turn_entity or state.just_asked:
            logger.primary_info(f'cur_entity changed from previous turn, so not asking a second question')
            return emptyResult(state)

        category_name = state.cur_category_name

        # # Otherwise, the cur_entity is still the category entity we set at the end of the previous turn e.g. 'Food'
        # # In this case, get another unasked question for the category and ask it with WEAK_CONTINUE
        # priority = ResponsePriority.WEAK_CONTINUE
        
        # question = state.get_first_category_response(category_name, state_manager)  # CategoryQuestion or None
        # if question:
        #     logger.primary_info(f'cur_entity {entity_tracker_state.cur_entity} is still the category entity we set at '
        #                         f'the end of the last turn, so asking a followup question on {category_name}')
        #     question_str = None
        #     if question.statement is None:
        #         question_str = question.question
        #     elif question.question is None:
        #         question_str = question.statement
        #     else:
        #         question_str = ' '.join((question.statement, question.question))
        #     response = choice(ACKNOWLEDGE_AND_ASK_SECOND_QUESTION).format(
        #         CATEGORYNAME2CLASS[category_name].activation_phrases[0], question_str)  # this is a hack to get a more natural-sounding name for the category
        #     cur_entity = get_entity_by_wiki_name(question.cur_entity_wiki_name, state_manager.current_state)
        #     conditional_state = ConditionalState(HandleAnswerTreelet.__name__, category_name, question.statement, question.question)
        #     return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=False,
        #                                 state=state, cur_entity=cur_entity, expected_type=question.expected_type,
        #                                 conditional_state=conditional_state)

        # else:
        #     logger.primary_info(f'No unasked questions left for category "{category_name}", so returning empty result')
        #     return emptyResult(state)

        # If the entity does not change, i.e. Entity Linker may not have been triggered, 
        # and CATEGORY RG has not responded, we want to use Regex / GPT2 to generate a good response, then ask for prompt from another RG.

        text = "Thanks for answering my questions!" # Default response that will be overwritten!
        cur_entity = prev_turn_entity
        conditional_state = ConditionalState(HandleAnswerTreelet.__name__, category_name, None, None, True)

        about_alexa = ""
        if WhatAboutYouTemplate().execute(state_manager.current_state.text) is not None:
            if "What TV show are you watching right now?" in state_manager.current_state.history[-1]:
                about_alexa = "I watched the office again. I've re-watched it so many times!"
            elif "What did you eat for dinner last night?" in state_manager.current_state.history[-1]:
                about_alexa = "I had some delicious spaghetti."
            else:
                about_alexa = state_manager.current_state.choose_least_repetitive(RESPONSE_TO_WHAT_ABOUT_YOU)
        
        if DontKnowTemplate().execute(state_manager.current_state.text) is not None:
            text = " ".join((state_manager.current_state.choose_least_repetitive(RESPONSE_TO_DONT_KNOW), about_alexa))
            cur_entity = None
        elif BackChannelingTemplate().execute(state_manager.current_state.text) is not None:
            text = " ".join((state_manager.current_state.choose_least_repetitive(RESPONSE_TO_BACK_CHANNELING), about_alexa))
            cur_entity = prev_turn_entity
        elif EverythingTemplate().execute(state_manager.current_state.text) is not None:
            text = " ".join((state_manager.current_state.choose_least_repetitive(RESPONSE_TO_EVERYTHING_ANS), about_alexa))
            cur_entity = prev_turn_entity
        elif NotThingTemplate().execute(state_manager.current_state.text) is not None:
            text = " ".join((state_manager.current_state.choose_least_repetitive(RESPONSE_TO_NOTHING_ANS), about_alexa))
            cur_entity = None

        else:
            if not hasattr(state_manager.current_state, 'gpt2ed'):
                logger.primary_info(f"CATEGORIES RG is running gpt2ed")
                default_gpt2ed_output = GPT2ED(state_manager).execute()
                setattr(state_manager.current_state, 'gpt2ed', default_gpt2ed_output)
            
            text = get_random_fallback_neural_response(state_manager.current_state)
            if text is None:
                return emptyResult(state)
            cur_entity = prev_turn_entity

        return ResponseGeneratorResult(text=text, priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                state=state, cur_entity=cur_entity, expected_type=None,
                                conditional_state=conditional_state)
