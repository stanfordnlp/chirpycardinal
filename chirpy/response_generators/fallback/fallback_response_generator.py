"""
Note: FALLBACK is an exception to the rule that you don't run the get_prompt() function of the RG that provided the response.
If FALLBACK provides the response, we still run its get_prompt() function, so that we always have a fallback prompt.
"""
import logging
import random

from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.regex.templates import (
    DontKnowTemplate,
    BackChannelingTemplate,
    EverythingTemplate,
    NotThingTemplate,
)
from chirpy.core.regex.response_lists import (
    RESPONSE_TO_DONT_KNOW,
    RESPONSE_TO_BACK_CHANNELING,
    RESPONSE_TO_EVERYTHING_ANS,
    RESPONSE_TO_NOTHING_ANS,
)
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, AnswerType
from chirpy.response_generators.fallback.state import *

logger = logging.getLogger('chirpylogger')

from chirpy.response_generators.fallback.response_templates import *

class FallbackResponseGenerator(ResponseGenerator):
    """
    A response generator that always provides a fallback response/prompt
    This is what is used if every other RG has nothing.
    """
    name='FALLBACK'
    def __init__(self, state_manager):
        super().__init__(state_manager, state_constructor=State, conditional_state_constructor=ConditionalState,
                         can_give_prompts=True)

    def handle_default_post_checks(self):
        logger.primary_info(f"Handling default post checks for {self.name}")
        state, utterance, response_types = self.get_state_utterance_response_types()
        text = None
        if self.get_last_active_rg() == self.name:
            if DontKnowTemplate().execute(utterance) is not None:
                text = self.choose(RESPONSE_TO_DONT_KNOW)
            elif BackChannelingTemplate().execute(utterance) is not None:
                text = self.choose(RESPONSE_TO_BACK_CHANNELING)
            elif EverythingTemplate().execute(utterance) is not None:
                text = self.choose(RESPONSE_TO_EVERYTHING_ANS)
            elif NotThingTemplate().execute(utterance) is not None:
                text = self.choose(RESPONSE_TO_NOTHING_ANS)
        else:
            if self.get_navigational_intent_output().pos_intent:
                text = self.choose(FALLBACK_POSNAV_RESPONSES)

        if text:
            return ResponseGeneratorResult(text=text, priority=ResponsePriority.WEAK_CONTINUE,
                                           needs_prompt=True, state=state, cur_entity=None,
                                           conditional_state=
                                           ConditionalState(used_fallback_response=state.used_fallback_response+1),
                                           answer_type=AnswerType.ENDING)
        else:
            return ResponseGeneratorResult(text=FALLBACK_RESPONSE, priority=ResponsePriority.UNIVERSAL_FALLBACK,
                                           needs_prompt=True, state=state, cur_entity=None,
                                           conditional_state=
                                           ConditionalState(used_fallback_response=state.used_fallback_response+1),
                                           answer_type=AnswerType.ENDING)

    def get_prompt(self, state) -> PromptResult:
        if self.state_manager.current_state.experiments.look_up_experiment_value('fallback') == 'no_question':
            return PromptResult(text=random.choice(FALLBACK_PROMPT_NO_QUESTIONS),
                                prompt_type=PromptType.GENERIC, state=state, cur_entity=None,
                                conditional_state=ConditionalState(used_fallback_prompt=state.used_fallback_response+1),
                                answer_type=AnswerType.ENDING)
        text = self.choose(FALLBACK_PROMPTS)
        return PromptResult(text=text, prompt_type=PromptType.GENERIC, state=state, cur_entity=None,
                            answer_type=AnswerType.QUESTION_HANDOFF,
                            conditional_state=ConditionalState(used_fallback_prompt=state.used_fallback_response+1))
