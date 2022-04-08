import logging
import random
import re

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType, AnswerType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.utils import WikiEntityInterface
from chirpy.response_generators.wiki2.wiki_utils import get_til_title
from chirpy.response_generators.music.state import ConditionalState
from chirpy.response_generators.music.music_helpers import ResponseType

logger = logging.getLogger('chirpylogger')


class GetInstrumentTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'music_get_instrument'
        self.can_prompt = True
        self.trigger_entity_groups = [ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_instrument]

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get Response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        response = None
        just_used_til = False

        entity = self.get_music_entity()
        if state.prev_treelet_str == self.name:
            if ResponseType.THATS in response_types and state.just_used_til:
                response = self.choose(RESPONSE_TO_THATS) + ' '
            elif ResponseType.DIDNT_KNOW in response_types and state.just_used_til:
                response = self.choose(RESPONSE_TO_DIDNT_KNOW) + ' '
            else:
                response = ''
            if entity is None:
                response += f'Say, I really wish I can learn to play it one day. It seems like a great instrument.'
            else:
                response += f'Say, I really wish I can learn to play the {entity.name} one day. It seems like a great instrument.'
            next_treelet_str, question = self.get_next_treelet()
            response += ' ' + question
        else:
            if entity:
                response = f'The {entity.name} is a really fascinating instrument!'
                tils = get_til_title(entity.name)
                if len(tils):
                    logger.primary_info(f'Found TILs {tils}')
                    til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
                    response += ' ' + process_til(til)
                    next_treelet_str = self.name
                    just_used_til = True
                else:
                    response += ' I wish I can learn to play it one day.'
                    next_treelet_str, question = self.get_next_treelet()
                    response += ' ' + question
            elif any(i in response_types for i in [
                    ResponseType.NO,
                    ResponseType.DONT_KNOW,
                    ResponseType.NOTHING,
                ]):
                response = 'It\'s alright, I think most people don\'t have a favorite instrument either. Maybe we can discuss another topic.'
                next_treelet_str, question = self.get_next_treelet()
                response += ' ' + question

        # Fallback if all else fails
        if response is None:
            response = 'I don\'t seem to recognize that instrument, maybe I need to go back to music class. Let\'s talk about something else then.'
            next_treelet_str, question = self.get_next_treelet()
            response += ' ' + question

        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str=next_treelet_str,
                                             just_used_til=just_used_til)
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
                                       cur_entity=entity, conditional_state=conditional_state)

    def get_prompt(self, **kwargs):
        # Might activate due to trigger entity
        state, utterance, response_types = self.get_state_utterance_response_types()
        entity = self.get_music_entity()
        just_used_til = False
        if entity:

            prompt_text = f'It\'s interesting that you mentioned the {entity.name}.'

            tils = get_til_title(entity.name)
            if len(tils):
                til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
                prompt_text += ' ' + process_til(til)
                next_treelet_str = self.name
                just_used_til = True
            else:
                prompt_text += ' I wish I can learn to play it one day.'
                next_treelet_str, question = self.get_next_treelet()
                prompt_text += ' ' + question
            prompt_type = PromptType.CURRENT_TOPIC

            conditional_state = ConditionalState(have_prompted=True,
                                                 prev_treelet_str=self.name,
                                                 next_treelet_str=next_treelet_str,
                                                 just_used_til=just_used_til)
            return PromptResult(text=prompt_text, prompt_type=prompt_type, state=state, cur_entity=entity,
                                conditional_state=conditional_state, answer_type=AnswerType.STATEMENT)

    def get_music_entity(self):
        def is_instrument(ent):
            return ent and WikiEntityInterface.is_in_entity_group(ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_instrument)
        cur_entity = self.rg.get_current_entity()
        entity_linker_results = self.rg.state_manager.current_state.entity_linker
        entities = []
        if cur_entity: entities.append(cur_entity)
        if len(entity_linker_results.high_prec): entities.append(entity_linker_results.high_prec[0].top_ent)
        if len(entity_linker_results.threshold_removed): entities.append(entity_linker_results.threshold_removed[0].top_ent)
        if len(entity_linker_results.conflict_removed): entities.append(entity_linker_results.conflict_removed[0].top_ent)
        for e in entities:
            if is_instrument(e): return e

    def get_next_treelet(self):
        next_treelet_str, question = random.choice([
            [self.rg.get_singer_treelet.name, ' How about musicians! Who is your favorite musician or band?'],
            [self.rg.get_song_treelet.name, ' How about songs! What is a favorite song you always listen to?'],
        ])
        return next_treelet_str, question
