from chirpy.annotators.blenderbot import BlenderBot
from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult
from chirpy.response_generators.neural_fallback.neural_helpers import get_random_fallback_neural_response
from chirpy.response_generators.neural_fallback.state import *
import logging

logger = logging.getLogger('chirpylogger')


class NeuralFallbackResponseGenerator(ResponseGenerator):
    """
    A response generator that provides a neural fallback response using the outputs from neural remote module
    This is what is used if every other RG (excluding FALLBACK) has nothing.
    """
    name='NEURAL_FALLBACK'
    def __init__(self, state_manager):
        super().__init__(state_manager, disallow_start_from=['LAUNCH'],
                         can_give_prompts=False, state_constructor=State,
                         conditional_state_constructor=ConditionalState)
        self.killable = True


    def handle_current_entity(self):
        # Don't run if the cur entity exists (isn't None) and is a non-category entity
        cur_entity = self.get_current_entity(initiated_this_turn=False)
        NON_CATEGORY_ENTITY = cur_entity is not None and not cur_entity.is_category
        if NON_CATEGORY_ENTITY:
            logger.info("entity_tracker.cur_entity exists and is not a category, skipping NeuralFallbackResponseGenerator")
            return self.emptyResult()

    def handle_default_post_checks(self): # TODO replace with neural response
        # If we haven't already run neural module in the NLP pipeline, run it now, and save it in the current state
        if not hasattr(self.state_manager.current_state, 'blenderbot'):
            default_neural_output = BlenderBot(self.state_manager).execute()
            setattr(self.state_manager.current_state, 'blenderbot', default_neural_output)
        logger.primary_info(f"NEURAL_FALLBACK received BlenderBot output {self.state_manager.current_state.blenderbot}")

        # Choose the best response and return it
        neural_fallback = get_random_fallback_neural_response(self.state_manager.current_state)
        if neural_fallback:
            return ResponseGeneratorResult(text=neural_fallback, priority=ResponsePriority.UNIVERSAL_FALLBACK,
                                           needs_prompt=True, state=self.state,
                                           cur_entity=self.get_current_entity(initiated_this_turn=False)
                                           )
        else:
            logger.primary_info("Didn't find a good neural fallback.")
            return self.emptyResult()

    def update_state_if_chosen(self, state: BaseState, conditional_state: Optional[BaseConditionalState]) -> BaseState:
        state.used_neural_fallback_response += 1
        return state

    # def update_state_if_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
    #     for key in ['used_neural_fallback_response']:
    #         if key in conditional_state and conditional_state[key]:
    #             state[key] += 1
    #     return state
