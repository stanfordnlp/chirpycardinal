import logging
import random
import re

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.response_generators.music.state import ConditionalState
from chirpy.response_generators.wiki2.wiki_utils import get_til_title


logger = logging.getLogger('chirpylogger')

def process_til(til):
    return random.choice([
        f'I found out that {til}. Isn\'t that interesting?',
        f'I learned that {til}. What do you think about that?',
        f'Did you know that {til}?',
        f'I just found out the other day that {til}. Isn\'t that fascinating? What do you think?',
    ])


class AskSingerTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'music_ask_singer'
        self.can_prompt = False

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get Response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        cur_song_str = self.rg.state.cur_song_str
        cur_singer_str = self.rg.state.cur_singer_str
        cur_singer_ent = self.rg.state.cur_singer_ent
        just_used_til = False

        response = None
        if state.prev_treelet_str != self.name:
            # Try to get a TIL
            response = None
            if cur_singer_str is None and cur_song_str is not None:
                metadata = self.rg.get_song_meta(cur_song_str)
                cur_singer_str = metadata['artist']
            if cur_singer_str:
                cur_singer_ent = self.rg.get_musician_entity(cur_singer_str)
            if cur_singer_ent:
                tils = get_til_title(cur_singer_ent.name)
                if len(tils):
                    logger.primary_info(f'Found TILs {tils}')
                    til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
                    response = process_til(til)
                    next_treelet_str = self.name
                    just_used_til = True

        if response is None:
            top_songs = self.rg.get_songs_by_musician(cur_singer_str)
            next_song = None
            for next_song in top_songs:
                if next_song != cur_song_str:
                    break
            if next_song:
                response = f'Oh I really love {next_song} by {cur_singer_str} too! Do you like it as well?'
                next_treelet_str = self.rg.handoff_treelet.name
            else:
                response = f'{cur_singer_str} seems to be really talented! Do you like any other songs by {cur_singer_str}?'
                next_treelet_str = self.rg.handoff_treelet.name

        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str=next_treelet_str,
                                             cur_singer_str=cur_singer_str,
                                             cur_singer_ent=cur_singer_ent,
                                             just_used_til=just_used_til,
                                             )
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
                                       cur_entity=cur_singer_ent, conditional_state=conditional_state)
