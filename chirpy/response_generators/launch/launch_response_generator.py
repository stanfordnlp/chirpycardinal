from typing import Optional
import logging

from chirpy.core.callables import ResponseGenerator
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, emptyResult, PromptResult, emptyPrompt, \
    UpdateEntity
from chirpy.response_generators.launch.launch_utils import ConditionalState, State, Treelet
from chirpy.response_generators.launch.treelets.first_turn_treelet import FirstTurnTreelet
from chirpy.response_generators.launch.treelets.handle_name_treelet import HandleNameTreelet

logger = logging.getLogger('chirpylogger')

# dict mapping name (str) to Treelet class
NAME2TREELET = {treelet.__name__: treelet for treelet in (FirstTurnTreelet, HandleNameTreelet)}

class LaunchResponseGenerator(ResponseGenerator):
    name='LAUNCH'
    """
    This RG deals with first few turns
    """

    def init_state(self) -> State:
        # if state_manager says it's first turn, set next_treelet to be FirstTurnTreelet
        if self.state_manager.last_state is None:
            return State('FirstTurnTreelet')

        # if state_manager says it's not first turn, then we're running init_state because LAUNCH failed.
        # set to OFF so that we don't start the launch sequence again.
        else:
            return State(None)

    def get_entity(self, state) -> UpdateEntity:
        return UpdateEntity(False)

    def get_response(self, state: State) -> ResponseGeneratorResult:
        if state.next_treelet is None:
            return emptyResult(state)
        next_treelet = NAME2TREELET[state.next_treelet]  # Treelet class
        return next_treelet(self).get_response(state)

    def get_prompt(self, state: State) -> PromptResult:
        return emptyPrompt(state)

    def update_state_if_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        assert conditional_state is not None, "conditional_state should not be None if the response/prompt was chosen"
        state.update_if_chosen(conditional_state)
        return state

    def update_state_if_not_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        state.update_if_not_chosen()
        return state

