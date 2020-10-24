from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from enum import Enum

# Types of response that we might expect from the user
class UserIntent(Enum):
    no = 1
    yes = 2
    yes_without_name = 3
    repeat = 4
    why = 5


@dataclass
class ConditionalState:
    next_treelet: Optional[str]  # the name of the treelet we should run on the next turn. None means turn off next turn.
    user_intent: Optional[UserIntent] = None # determines if the user wants to give name or not


@dataclass
class State:
    next_treelet: Optional[str]  # the name of the treelet we should run on the next turn. None means turn off next turn.
    asked_name_counter: int = 0  # how many times we've asked the user's name

    def update_if_chosen(self, conditional_state: ConditionalState):
        """If our response/prompt has been chosen, update state using conditional state"""
        self.next_treelet = conditional_state.next_treelet
        if self.next_treelet == 'HandleNameTreelet':
            if conditional_state.user_intent != UserIntent.yes_without_name:
                self.asked_name_counter += 1
            if conditional_state.user_intent == UserIntent.repeat:
                self.asked_name_counter = 1

    def update_if_not_chosen(self):
        """If our response/prompt has not been chosen, update state"""
        self.next_treelet = None

class Treelet(ABC):

    def __init__(self, rg):
        self.state_manager = rg.state_manager

    @abstractmethod
    def get_response(self, state: State) -> ResponseGeneratorResult:
        pass

    @abstractmethod
    def get_prompt(self, state: State) -> PromptResult:
        pass