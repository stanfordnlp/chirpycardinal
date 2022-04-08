import logging
import random
import re

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType
from chirpy.response_generators.music.regex_templates import NameFavoriteSongTemplate
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.response_generators.music.utils import WikiEntityInterface
from chirpy.response_generators.wiki2.wiki_utils import get_til_title
import chirpy.response_generators.music.response_templates.general_templates as templates
from chirpy.response_generators.music.state import ConditionalState
from chirpy.response_generators.music.music_helpers import ResponseType

logger = logging.getLogger('chirpylogger')


class GetSingerTreelet(Treelet):
    def __init__(self, rg):
        super().__init__(rg)
        self.name = 'music_get_singer'
        self.can_prompt = True
        self.trigger_entity_groups = [ENTITY_GROUPS_FOR_EXPECTED_TYPE.musician]

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get Response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        cur_singer_ent = None
        cur_singer_str = None
        response = None
        just_used_til = False

        cur_singer_ent = self.get_music_entity()
        if cur_singer_ent:
            cur_singer_str = cur_singer_ent.talkable_name
            cur_singer_str = re.sub(r'\(.*?\)', '', cur_singer_str)
            response = self.choose(templates.compliment_user_musician_choice())
            if WikiEntityInterface.is_in_entity_group(cur_singer_ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_group):
                response += f' {cur_singer_str} is definitely a great group!'
            else:
                response += f' {cur_singer_str} is definitely a great musician!'
            tils = get_til_title(cur_singer_ent.name)
            if len(tils):
                logger.primary_info(f'Found TILs {tils}')
                til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
                response += ' ' + templates.til(til)
                just_used_til = True
            else:
                singer_comment, _ = self.comment_singer(cur_singer_str)
                response += ' ' + singer_comment
            next_treelet_str = self.rg.ask_song_treelet.name
        elif any(i in response_types for i in [
                ResponseType.NO,
                ResponseType.DONT_KNOW,
                ResponseType.NOTHING,
                ResponseType.NEGATIVE,
            ]):
            response = 'Yeah it can be hard to pick a particular musician when there are so many. How about a favorite song? Do you have a song you really like?'
            next_treelet_str = self.rg.get_song_treelet.name
        else:
            # Try to parse singer name from utterance
            slots = NameFavoriteSongTemplate().execute(utterance)
            if slots is not None and 'favorite' in slots:
                cur_singer_str = slots['favorite']
                cur_singer_ent = self.rg.get_song_entity(cur_singer_str)
                response = self.choose(templates.compliment_user_musician_choice())
                if cur_singer_ent:
                    if WikiEntityInterface.is_in_entity_group(cur_singer_ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_group):
                        response += f' {cur_singer_str} is a great band!'
                    else:
                        response += f' {cur_singer_str} is a great musician!'
                    tils = get_til_title(cur_singer_ent.name)
                    if len(tils):
                        logger.primary_info(f'Found TILs {tils}')
                        til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
                        response += ' ' + templates.til(til)
                        next_treelet_str = self.rg.ask_song_treelet.name
                        just_used_til = True
                    else:
                        cur_singer_str = re.sub(r'\(.*?\)', '', cur_singer_ent.talkable_name)
                        singer_comment, _ = self.comment_singer(cur_singer_str)
                        response += ' ' + singer_comment
                        next_treelet_str = self.rg.ask_song_treelet.name
                else:
                    response += f' I love {cur_singer_str} too!'
                    singer_comment, genre = self.comment_singer(cur_singer_str)
                    if genre is None:
                        response = 'Oh I don\'t seem to recognize that artist, I definitely need to get out more. How about a favorite song? Do you have a song you really like?'
                        next_treelet_str = self.rg.get_song_treelet.name
                    else:
                        response += ' ' + singer_comment
                        next_treelet_str = self.rg.ask_song_treelet.name

        # Fallback if all else fails
        if response is None:
            response = 'Oh I don\'t seem to recognize that artist, I definitely need to get out more. How about a favorite song? Do you have a song you really like?'
            next_treelet_str = self.rg.get_song_treelet.name

        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str=next_treelet_str,
                                             just_used_til=just_used_til)
        if cur_singer_str is not None:
            conditional_state.cur_singer_str = cur_singer_str
        if cur_singer_ent is not None:
            conditional_state.cur_singer_ent = cur_singer_ent
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
                                       cur_entity=cur_singer_ent, conditional_state=conditional_state)

    def get_prompt(self, **kwargs):
        # Might activate due to trigger entity
        state, utterance, response_types = self.get_state_utterance_response_types()
        cur_singer_ent = self.get_music_entity()
        just_used_til = False
        
        if cur_singer_ent:
            cur_singer_str = cur_singer_ent.talkable_name
            cur_singer_str = re.sub(r'\(.*?\)', '', cur_singer_str)
            prompt_text = f'I love that you brought up {cur_singer_str}.'

            tils = get_til_title(cur_singer_ent.name)
            if len(tils):
                til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
                prompt_text += ' ' + templates.til(til)
                just_used_til = True
            else:
                singer_comment, _ = self.comment_singer(cur_singer_str)
                prompt_text += ' ' + singer_comment
            prompt_type = PromptType.CURRENT_TOPIC
            next_treelet_str = self.rg.ask_song_treelet.name

            conditional_state = ConditionalState(have_prompted=True,
                                                 prev_treelet_str=self.name,
                                                 next_treelet_str=next_treelet_str,
                                                 just_used_til=just_used_til)
            if cur_singer_str is not None:
                conditional_state.cur_singer_str = cur_singer_str
            if cur_singer_ent is not None:
                conditional_state.cur_singer_ent = cur_singer_ent
        
            return PromptResult(text=prompt_text, prompt_type=prompt_type, state=state, cur_entity=cur_singer_ent,
                                conditional_state=conditional_state)

    def get_music_entity(self):
        def is_singer(ent):
            return ent and WikiEntityInterface.is_in_entity_group(ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musician)
        cur_entity = self.rg.get_current_entity()
        entity_linker_results = self.rg.state_manager.current_state.entity_linker
        entities = []
        if cur_entity: entities.append(cur_entity)
        if len(entity_linker_results.high_prec): entities.append(entity_linker_results.high_prec[0].top_ent)
        if len(entity_linker_results.threshold_removed): entities.append(entity_linker_results.threshold_removed[0].top_ent)
        if len(entity_linker_results.conflict_removed): entities.append(entity_linker_results.conflict_removed[0].top_ent)
        for e in entities:
            if is_singer(e): return e

    def comment_singer(self, singer_name):
        """
        Make a relevant comment about the singer and returns (comment, genre)
        """
        genre = self.rg.get_singer_genre(singer_name)
        if genre:
            return self.choose([
                f'{singer_name} does really fabulous {genre} songs right?',
                f'The {genre} songs by {singer_name} are really good right?',
            ]), genre
        return self.choose([
            f'{singer_name} does really nice songs right?',
            f'{singer_name} has some really good tunes right?',
        ]), genre
