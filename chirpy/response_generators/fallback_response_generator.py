"""
Note: FALLBACK is an exception to the rule that you don't run the get_prompt() function of the RG that provided the response.
If FALLBACK provides the response, we still run its get_prompt() function, so that we always have a fallback prompt.
"""
import logging
import random
from typing import Optional

from chirpy.core.callables import ResponseGenerator
from chirpy.core.regex.templates import DontKnowTemplate, RESPONSE_TO_DONT_KNOW, RESPONSE_TO_BACK_CHANNELING, \
    BackChannelingTemplate, RESPONSE_TO_EVERYTHING_ANS, EverythingTemplate, RESPONSE_TO_NOTHING_ANS, NotThingTemplate
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, UpdateEntity

logger = logging.getLogger('chirpylogger')

FALLBACK_RESPONSE = "Sorry, I'm not sure how to answer that."

FALLBACK_PROMPTS = [
    "I just wanted you to know that I'm really enjoying talking with you so far. I'd love to get to know you better. What are you interested in?",
    "By the way, there's so much information up here in the cloud that I can share with you. What's something you'd like to know more about?",
    "Anyway, it's great getting to know you more. If you don't mind me asking, what have you been interested in lately?",
    "Since quarantine started, I've been using my free time to learn new things. I'd be happy to share them with you. What would you like to learn more about?"
]
FALLBACK_PROMPT_NO_QUESTIONS = ["By the way, I\'m glad to get to talk with you.",
                                "It\'s lovely talking to you.",
                                "It\'s great getting to know you better."]

class FallbackResponseGenerator(ResponseGenerator):
    name='FALLBACK'
    """
    A response generator that always provides a fallback response/prompt
    This is what is used if every other RG has nothing.
    """

    def init_state(self) -> dict:

        # init some counters to count how many times we use the fallback response/prompt
        return {
            'used_fallback_response': 0,
            'used_fallback_prompt': 0,
        }

    def get_entity(self, state) -> UpdateEntity:
        return UpdateEntity(False)

    def get_response(self, state: dict) -> ResponseGeneratorResult:
        state_manager = self.state_manager
        text = None
        if state_manager.last_state_active_rg == 'FALLBACK':
            if DontKnowTemplate().execute(state_manager.current_state.text) is not None:
                text = state_manager.current_state.choose_least_repetitive(RESPONSE_TO_DONT_KNOW)
            elif BackChannelingTemplate().execute(state_manager.current_state.text) is not None:
                text = state_manager.current_state.choose_least_repetitive(RESPONSE_TO_BACK_CHANNELING)
            elif EverythingTemplate().execute(state_manager.current_state.text) is not None:
                text = state_manager.current_state.choose_least_repetitive(RESPONSE_TO_EVERYTHING_ANS)
            elif NotThingTemplate().execute(state_manager.current_state.text) is not None:
                text = state_manager.current_state.choose_least_repetitive(RESPONSE_TO_NOTHING_ANS)

        if text:
            return ResponseGeneratorResult(text=text, priority=ResponsePriority.WEAK_CONTINUE,
                                           needs_prompt=True, state=state, cur_entity=None,
                                           conditional_state={'used_fallback_response': True})
        else:
            return ResponseGeneratorResult(text=FALLBACK_RESPONSE, priority=ResponsePriority.UNIVERSAL_FALLBACK,
                                           needs_prompt=True, state=state, cur_entity=None,
                                           conditional_state={'used_fallback_response': True})

    def get_prompt(self, state: dict) -> PromptResult:
        if self.state_manager.current_state.experiments.look_up_experiment_value('fallback') == 'no_question':
            return PromptResult(text=random.choice(FALLBACK_PROMPT_NO_QUESTIONS), 
                                prompt_type=PromptType.GENERIC, state=state, cur_entity=None,
                                conditional_state={'used_fallback_prompt': True})
        text = self.state_manager.current_state.choose_least_repetitive(FALLBACK_PROMPTS)
        return PromptResult(text=text, prompt_type=PromptType.GENERIC, state=state, cur_entity=None,
                                conditional_state={'used_fallback_prompt': True})


    def update_state_if_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        for key in ['used_fallback_response', 'used_fallback_prompt']:
            if key in conditional_state and conditional_state[key]:
                state[key] += 1
        return state

    def update_state_if_not_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return state

