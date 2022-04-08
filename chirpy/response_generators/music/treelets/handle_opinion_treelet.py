import logging
import random

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType, AnswerType
from chirpy.response_generators.music.response_templates import handle_opinion_template
from chirpy.response_generators.music.music_helpers import ResponseType
from chirpy.response_generators.music.state import ConditionalState

logger = logging.getLogger('chirpylogger')


class HandleOpinionTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'music_handle_opinion'
        self.can_prompt = True

    def get_trigger_response(self, **kwargs):
        # Triggered by KEYWORD_MUSIC
        logger.primary_info(f'{self.name} - Triggered')
        state, utterance, response_types = self.get_state_utterance_response_types()
        if ResponseType.YES in response_types:
            priority = ResponsePriority.CAN_START
            response = handle_opinion_template.HandleLikeMusicResponseTemplate().sample()
            next_treelet_str, question = self.get_next_treelet()
            return ResponseGeneratorResult(
                text=response+question, needs_prompt=False, cur_entity=None,
                priority=priority,
                state=self.rg.state, conditional_state=ConditionalState(
                    prev_treelet_str=self.name,
                    next_treelet_str=next_treelet_str,
                ),
                answer_type=AnswerType.QUESTION_SELFHANDLING
            )

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        if ResponseType.FREQ in response_types:
            if 'everyday' in utterance:
                response = 'Well for me, I love listening to music everyday too!'
            else:
                response = 'Well for me, I love listening to music everyday!'
            next_treelet_str, question = self.get_next_treelet()
            response += ' ' + question
            answer_type = AnswerType.QUESTION_SELFHANDLING
        elif (ResponseType.NO in response_types or ResponseType.NEGATIVE in response_types) and not ResponseType.DONT_KNOW in response_types:
            response = 'No problem! Everyone has different interests and it sounds like music isn\'t your thing.'
            response, needs_prompt, next_treelet_str = self.rg.try_talking_about_fav_song_else_exit(response)
            answer_type = AnswerType.NONE
        elif ResponseType.DONT_KNOW in response_types:
            response = 'It\'s okay, sometimes I am not sure how I feel about music either. But in some ways, ' \
                       'music is tremendously fascinating. A physical dancing of air molecules that translates to ' \
                       'figurative dancing of neurons. But philosophical musings aside, '
            next_treelet_str, question = self.get_next_treelet()
            response += ' ' + question
            answer_type = AnswerType.QUESTION_SELFHANDLING
        elif ResponseType.YES in response_types or ResponseType.POSITIVE in response_types or ResponseType.MUSIC_RESPONSE in response_types:
            response = handle_opinion_template.HandleLikeMusicResponseTemplate().sample()
            next_treelet_str, question = self.get_next_treelet()
            response += ' ' + question
            answer_type = AnswerType.QUESTION_SELFHANDLING
        else: # For now we only recognize yes/no/idk replies
            response = 'Okay, sure!'
            needs_prompt = True
            next_treelet_str = 'exit'
            answer_type = AnswerType.NONE
            
        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str=next_treelet_str)
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
                                       cur_entity=None,
                                       conditional_state=conditional_state,
                                       answer_type=answer_type)

    def get_prompt(self, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if state.have_prompted:
            return None
        if ResponseType.MUSIC_KEYWORD in response_types and \
           ResponseType.POSITIVE in response_types:
            prompt_type = PromptType.CONTEXTUAL
            prompt_text = handle_opinion_template.HandleLikeMusicPromptTemplate().sample()
            next_treelet_str, question = self.get_next_treelet()
            return PromptResult(text=prompt_text+question, prompt_type=prompt_type, state=state, cur_entity=None,
                            conditional_state=ConditionalState(
                                have_prompted=True,
                                prev_treelet_str=self.name,
                                next_treelet_str=next_treelet_str
                            ))

    def get_next_treelet(self):
        next_treelet_str, question = random.choice([
            [self.rg.get_instrument_treelet.name, ' There are so many instruments in the world. What is your favorite one?'],
            [self.rg.get_singer_treelet.name, ' Do you have a favorite singer? Who is it?'],
            [self.rg.get_song_treelet.name, ' What is a song you love listening to?'],
        ])
        return next_treelet_str, question
