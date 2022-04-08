import logging
import random

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType
from chirpy.response_generators.music.music_helpers import ResponseType
from chirpy.response_generators.music.state import ConditionalState

logger = logging.getLogger('chirpylogger')


class IntroductoryTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'music_introductory'
        self.can_prompt = True

    def get_trigger_response(self, **kwargs):
        # Triggered by KEYWORD_MUSIC
        logger.primary_info(f'{self.name} - Triggered')
        state, utterance, response_types = self.get_state_utterance_response_types()

        priority = self.rg._get_priority_from_answer_type()
        response = random.choice([
            'Music is one of my favorite things and I was wondering if we could talk about it.',
            'There\'s so much music here in the cloud and I\'m curious to know what you think about it.',
        ])
        next_treelet_str, question = self.get_next_treelet()
        return ResponseGeneratorResult(
            text=response+question, needs_prompt=False, cur_entity=None,
            priority=priority,
            state=state, conditional_state=ConditionalState(
                prev_treelet_str=self.name,
                next_treelet_str=next_treelet_str,
            ),
        )

    def get_prompt(self, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if state.have_prompted:
            return None
        if ResponseType.MUSIC_KEYWORD in response_types and \
           not ResponseType.POSITIVE in response_types:
            # If ResponseType.POSITIVE, we will prompt via HandleOpinionTreelet
            prompt_type = PromptType.CONTEXTUAL
            prompt_text = 'I love how you mentioned music! I\'ve been listening to a lot of new songs lately, and I\'d love to hear what you think.'
        else:
            prompt_type = PromptType.GENERIC
            prompt_text = 'By the way, I\'ve been listening to a lot of new songs lately, and I\'d love to hear what you think.'
        next_treelet_str, question = self.get_next_treelet()
        return PromptResult(text=prompt_text+question, prompt_type=prompt_type, state=state, cur_entity=None,
                            conditional_state=ConditionalState(
                                have_prompted=True,
                                prev_treelet_str=self.name,
                                next_treelet_str=next_treelet_str,
                            ))

    def get_next_treelet(self):
        next_treelet_str, question = random.choice([
            [self.rg.handle_opinion_treelet.name, ' Do you like music too?'],
            [self.rg.handle_opinion_treelet.name, ' Do you listen to music often?'],
        ])
        return next_treelet_str, question
