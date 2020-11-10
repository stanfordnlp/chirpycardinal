from enum import Enum
from abc import ABC, abstractmethod
import random
from typing import Dict, List

from chirpy.core.entity_linker.entity_linker_classes import WikiEntity

from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt

from chirpy.response_generators.music.utils import logger
from chirpy.response_generators.music.state import State, ConditionalState
from chirpy.response_generators.music.expression_lists import HANDOFF_REMARKS

# Helper method imports from other RGs
from chirpy.response_generators.neural_helpers import get_neural_fallback_handoff


class TreeletType(Enum):
    HEAD = 0
    CHILD = 1


class Treelet(ABC):

    def __init__(self, rg):
        self.state_manager = rg.state_manager
        self.name = None
        self.repr = None
        self.treelet_type = TreeletType.CHILD
        self.trigger_phrases = []
        self.trigger_entity_groups = []
        self.templates = {}

    def __name__(self):
        return self.name

    def __repr__(self):
        return self.repr

    @abstractmethod
    def get_trigger_phrases(self) -> List[str]:
        pass

    @abstractmethod
    def get_trigger_entity_groups(self) -> List[str]:
        pass

    def get_response(self, state: State, trigger_entity: WikiEntity = None, trigger_phrase: str = None) -> ResponseGeneratorResult:
        if state.last_turn_asked_question:
            response = self.get_response_last_turn_asked_question(state)
        elif trigger_entity:
            response = self.get_response_trigger_entity(state, trigger_entity)
        elif trigger_phrase:
            response = self.get_response_trigger_phrase(state, trigger_phrase)
        else:
            error_message = f"{self.name} was selected to respond, but neither of the conditions are met: last_turn_asked_question, trigger_entity, or trigger_phrase."
            logger.error(error_message)
            response = self.get_handoff_response(self.state_manager, state)

        response.conditional_state.turn_treelet_history.append(self.name)

        return response

    def get_response_last_turn_asked_question(self, state: State) -> ResponseGeneratorResult:
        error_message = f"Method get_response_last_turn_asked_question of {self.name} was selected to respond, but it is not implemented."
        logger.error(error_message)
        return self.get_handoff_response(self.state_manager, state)

    def get_response_trigger_entity(self, state: State, trigger_entity: WikiEntity = None) -> ResponseGeneratorResult:
        error_message = f"Method get_response_trigger_entity of {self.name} was selected to respond, but it is not implemented."
        logger.error(error_message)
        return self.get_handoff_response(self.state_manager, state)

    def get_response_trigger_phrase(self, state: State, trigger_phrase: str = None) -> ResponseGeneratorResult:
        error_message = f"Method get_response_trigger_phrase of {self.name} was selected to respond, but it is not implemented."
        logger.error(error_message)
        return self.get_handoff_response(self.state_manager, state)

    def get_prompt(self, state: State, conditional_state: ConditionalState = None, trigger_entity: WikiEntity = None) -> PromptResult:
        return emptyPrompt(state)

    def choose(self, items):
        # return self.state_manager.choose_least_repetitive(items)
        return random.choice(items)

    def is_no_answer(self):
        is_no_answer = self.state_manager.current_state.dialog_act['is_no_answer']
        return is_no_answer

    def is_yes_answer(self):
        is_yes_answer = self.state_manager.current_state.dialog_act['is_yes_answer']
        return is_yes_answer

    @staticmethod
    def get_handoff_response(state_manager, state):
        neural_response = get_neural_fallback_handoff(state_manager.current_state)
        text = neural_response or random.choice(HANDOFF_REMARKS)
        priority = ResponsePriority.WEAK_CONTINUE
        response = Treelet.prepare_rg_result(text, state, priority=priority, needs_prompt=True)
        return response

    @staticmethod
    def prepare_rg_result(text, state, priority=None, needs_prompt=False, cur_entity=None, conditional_state=None):
        if priority is None:
            priority = ResponsePriority.STRONG_CONTINUE if state.treelet_history else ResponsePriority.FORCE_START
        if conditional_state is None:
            conditional_state = ConditionalState()
            conditional_state.needs_internal_prompt = True
        rg_result = ResponseGeneratorResult(text=text, priority=priority, needs_prompt=needs_prompt,  state=state,
                                            cur_entity=cur_entity, conditional_state=conditional_state)
        return rg_result

    @staticmethod
    def prepare_prompt_result(text, state, priority=None, cur_entity=None, conditional_state=None):
        if priority is None:
            priority = PromptType.GENERIC
        if conditional_state is None:
            conditional_state = ConditionalState()
        prompt_result = PromptResult(text, priority, state, cur_entity, conditional_state=conditional_state)
        return prompt_result

    @staticmethod
    def get_template_name(template):
        return template.__class__.__name__

    @staticmethod
    def process_templates(templates, utterance) -> Dict[str, str]:
        triggered_templates = {}

        for template_name, template in templates.items():
            slots = template.execute(utterance)
            if slots: triggered_templates[template_name] = slots

        return triggered_templates

    def construct_response_from_templates(self, templates, template_name, question=False):
        # Construct our answer from the example answers
        response_template = templates[template_name]
        positive_examples = [question for (question, _) in response_template.positive_examples]
        response = self.choose(positive_examples)
        punctuation = '?' if question else '.'
        response = response.capitalize() + punctuation
        return response
