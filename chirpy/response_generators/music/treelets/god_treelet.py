import logging
import random

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType, AnswerType
from chirpy.response_generators.music.response_templates import handle_opinion_template
from chirpy.response_generators.music.music_helpers import ResponseType
from chirpy.response_generators.music.state import ConditionalState

logger = logging.getLogger('chirpylogger')


class GodTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'god_treelet'
        self.can_prompt = True

    def get_trigger_response(self, **kwargs):
        # Triggered by KEYWORD_MUSIC
        logger.primary_info(f'{self.name} - Triggered')
        state, utterance, response_types = self.get_state_utterance_response_types()
        if ResponseType.YES in response_types:
            priority = ResponsePriority.CAN_START
            response = handle_opinion_template.HandleLikeMusicResponseTemplate().sample()
            # next_treelet_str, question = self.get_next_treelet()
            return ResponseGeneratorResult(
                text=response+question, needs_prompt=False, cur_entity=None,
                priority=priority,
                state=self.rg.state, conditional_state=ConditionalState(
                    prev_treelet_str=self.name,
                    next_treelet_str=self.name,
                ),
                answer_type=AnswerType.QUESTION_SELFHANDLING
            )

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        # YAML parse logic here
        return ResponseGeneratorResult(text=response, priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False, state=state,
                                       cur_entity=None,
                                       conditional_state=None,
                                       answer_type=AnswerType.QUESTION_SELFHANDLING)

    def get_prompt(self, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        # YAML processing for prompt treelet leading question
        return PromptResult(text=prompt_text+question, prompt_type=PromptType.CONTEXTUAL, state=state, cur_entity=None,
                        conditional_state=ConditionalState(
                            have_prompted=True,
                            prev_treelet_str=self.name,
                            next_treelet_str=self.name
                        ))

