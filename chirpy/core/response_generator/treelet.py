from chirpy.core.response_generator_datatypes import emptyResult, ResponseGeneratorResult, emptyPrompt, ResponsePriority
from abc import ABC
import logging
from chirpy.core.response_generator.response_type import ResponseType
from chirpy.core.response_generator.state import BaseState, BaseConditionalState
from chirpy.core.response_generator.helpers import construct_response_types_tuple
logger = logging.getLogger('chirpylogger')

class Treelet(ABC):
    name = "default_treelet"

    def __init__(self, rg):
        super().__init__()
        self.rg: 'ResponseGenerator' = rg
        self.trigger_entity_groups = []

    def __repr__(self):
        return self.name

    def __name__(self):
        return self.name

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """Generates a ResponseGeneratorResult containing that treelet's response to the user.

        Args:
            state (State): representation of the RG's internal state; see state.py for definition.
            utterance (str): what the user just said
            response_types (ResponseTypes): type of response given by the user
            priority (ResponsePriority): five-level response priority tier.
            :param priority:
            :param **kwargs:
        """

    def get_trigger_response(self, **kwargs):
        return None # by default, can't respond

    def get_question_response(self):
        return None

    def get_prompt(self, **kwargs):
        return None

    def get_state_utterance_response_types(self):
        return self.rg.state, self.rg.utterance, self.rg.response_types

    def get_current_state(self):
        return self.rg.get_current_state()

    def get_current_entity(self, initiated_this_turn=False):
        return self.rg.get_current_entity(initiated_this_turn=initiated_this_turn)

    def get_sentiment(self):
        return self.rg.get_sentiment()

    def get_experiments(self):
        return self.rg.get_experiments()

    def get_experiment_by_lookup(self, experiment_name):
        return self.rg.get_experiment_by_lookup(experiment_name)

    def choose(self, items):
        return self.rg.state_manager.current_state.choose_least_repetitive(items)

    def emptyResult(self):
        return self.rg.emptyResult()

    def emptyPrompt(self):
        return self.rg.emptyPrompt()

    def get_neural_acknowledgement(self):
        return self.rg.get_neural_acknowledgement()

    def get_neural_response(self, prefix=None, allow_questions=False, conditions=None):
        return self.rg.get_neural_response(prefix=prefix, allow_questions=allow_questions, conditions=conditions)

    def construct_response_from_templates(self, templates, template_name, question=False):
        """Constructs an utterance from the positive examples in a template."""
        response_template = templates[template_name]
        positive_examples = [question for (question, _) in response_template.positive_examples]
        response = self.choose(positive_examples)
        punctuation = '?' if question else '.'
        response = response.capitalize() + punctuation
        return response
