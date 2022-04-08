from typing import Optional
import logging

from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, emptyResult, PromptResult, emptyPrompt, \
    UpdateEntity
from chirpy.response_generators.launch.launch_helpers import *
from chirpy.response_generators.launch.treelets import *
from chirpy.response_generators.launch.state import *

logger = logging.getLogger('chirpylogger')

class LaunchResponseGenerator(ResponseGenerator):
    """
    This RG deals with first few turns
    """
    name = 'LAUNCH'
    def __init__(self, state_manager) -> None:
        self.first_turn_treelet = FirstTurnTreelet(self)
        self.handle_name_treelet = HandleNameTreelet(self)
        self.recognized_name_treelet = RecognizedNameTreelet(self)
        treelets = {
            treelet.name: treelet for treelet in [self.first_turn_treelet, self.handle_name_treelet,
                                                  self.recognized_name_treelet]
        }
        super().__init__(state_manager, can_give_prompts=False, treelets=treelets, state_constructor=State,
                         conditional_state_constructor=ConditionalState)

    def handle_default_pre_checks(self):
        if self.state_manager.last_state is None:
            return self.treelets[self.state.next_treelet_str].get_response()

    def init_state(self) -> State:
        # if state_manager says it's first turn, set next_treelet to be FirstTurnTreelet
        if self.state_manager.last_state is None:
            return State(next_treelet_str=self.first_turn_treelet.name)

        # if state_manager says it's not first turn, then we're running init_state because LAUNCH failed.
        # set to OFF so that we don't start the launch sequence again.
        else:
            return State(next_treelet_str=None)

    def update_state_if_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> BaseState:
        assert conditional_state is not None, "conditional_state should not be None if the response/prompt was chosen"
        state = super().update_state_if_chosen(state, conditional_state)
        if conditional_state.next_treelet_str == self.handle_name_treelet.name:
            # if conditional_state.user_intent == UserIntent.yes_without_name:
            state.asked_name_counter += 1
            # if conditional_state.user_intent == UserIntent.repeat:
            # state.asked_name_counter = 1
        return state

    def update_state_if_not_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> BaseState:
        state = super().update_state_if_not_chosen(state, conditional_state)
        state.next_treelet_str = None
        return state
