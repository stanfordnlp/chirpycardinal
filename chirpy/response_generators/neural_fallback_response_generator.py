from typing import Optional

from chirpy.annotators.gpt2ed import GPT2ED
from chirpy.core.callables import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyResult, emptyPrompt, \
    UpdateEntity
from chirpy.response_generators.neural_helpers import get_random_fallback_neural_response
import logging
import random

logger = logging.getLogger('chirpylogger')

RGS_NOT_USING_CUR_ENTITY = {'LAUNCH', 'OPINION'}

class NeuralFallbackResponseGenerator(ResponseGenerator):
    name='NEURAL_FALLBACK'
    """
    A response generator that provides a neural fallback response using the outputs from GPT2ED remote module
    This is what is used if every other RG (excluding FALLBACK) has nothing.
    """

    def init_state(self) -> dict:

        # init some counters to count how many times we use the fallback response/prompt
        return {
            'used_neural_fallback_response': 0,
        }

    def get_entity(self, state) -> UpdateEntity:
        return UpdateEntity(False)

    def get_response(self, state: dict) -> ResponseGeneratorResult:

        # Don't run if the cur entity exists (isn't None) and is a non-category entity
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity
        NON_CATEGORY_ENTITY = cur_entity is not None and not cur_entity.is_category
        if NON_CATEGORY_ENTITY:
            logger.info("entity_tracker.cur_entity exists and is not a category, skipping NeuralFallbackResponseGenerator")
            return emptyResult(state=state)

        # Don't run if LAUNCH RG is the currently active RG or if this is the first turn
        LAUNCH_ACTIVE = (self.state_manager.last_state_active_rg == 'LAUNCH' and self.state_manager.last_state.response_generator_states['LAUNCH'].next_treelet) or len(self.state_manager.current_state.history)<=1
        if LAUNCH_ACTIVE:
            logger.info("LAUNCH RG active, skipping NeuralFallbackResponseGenerator")
            return emptyResult(state=state)

        # Don't run if OPINION, NEURAL_CHAT, CATEGORIES is currently active
        if self.state_manager.last_state_active_rg in {'OPINION', 'NEURAL_CHAT', 'CATEGORIES'}:
            logger.info("self.state_manager.last_state_active_rg RG active, skipping NeuralFallbackResponseGenerator")
            return emptyResult(state=state)

        # If we haven't already run gpt2ed in the NLP pipeline, run it now, and save it in the current state
        if not hasattr(self.state_manager.current_state, 'gpt2ed'):
            default_gpt2ed_output = GPT2ED(self.state_manager).execute()
            setattr(self.state_manager.current_state, 'gpt2ed', default_gpt2ed_output)

        # Choose the best response and return it
        neural_fallback = get_random_fallback_neural_response(self.state_manager.current_state)
        if neural_fallback:
            return ResponseGeneratorResult(text=neural_fallback, priority=ResponsePriority.UNIVERSAL_FALLBACK,
                                           needs_prompt=True, state=state,
                                           cur_entity=self.state_manager.current_state.entity_tracker.cur_entity,
                                           conditional_state={'used_neural_fallback_response': True})
        else:
            return emptyResult(state=state)

    def get_prompt(self, state: dict) -> PromptResult:
        return emptyPrompt(state=state)


    def update_state_if_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        for key in ['used_neural_fallback_response']:
            if key in conditional_state and conditional_state[key]:
                state[key] += 1
        return state

    def update_state_if_not_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return state

