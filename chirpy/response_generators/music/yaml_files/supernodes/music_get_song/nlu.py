import logging
import random
import re

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.regex_templates.name_favorite_song_template import NameFavoriteSongTemplate
from chirpy.response_generators.music.utils import WikiEntityInterface
from chirpy.response_generators.wiki2.wiki_utils import get_til_title
import chirpy.response_generators.music.response_templates.general_templates as templates
from chirpy.response_generators.music.state import ConditionalState
from chirpy.response_generators.music.music_helpers import ResponseType

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'song_ent_exists': False,
        'dont_know': False,
        'no_fav_song': False,
        'tils_exist': False,
        'metadata_exists': False
    }

    cur_singer_str = None
    cur_song_str = None
    cur_song_ent = None
    # if cur_song_str is not None:
 #            conditional_state.cur_song_str = cur_song_str
 #    if cur_song_ent is not None:
 #        conditional_state.cur_song_ent = cur_song_ent
 #    if cur_singer_str is not None:

    cur_song_ent, cur_singer_ent = rg.get_song_and_singer_entity()
    if cur_song_ent:
        flags['song_ent_exists'] = True
        cur_song_str = cur_song_ent.talkable_name
        cur_song_str = re.sub(r'\(.*?\)', '', cur_song_str)
        tils = get_til_title(cur_song_ent.name)
        if len(tils):
            flags['tils_exist'] = True
        else:
            metadata = rg.get_song_meta(cur_song_str, cur_singer_ent.talkable_name if cur_singer_ent else None)
            if metadata:
                flags['metadata_exists'] = True
                cur_singer_str = metadata['artist']
    elif ResponseType.DONT_KNOW in response_types:
        flags['dont_know'] = True
    elif ResponseType.NO in response_types or ResponseType.NOTHING in response_types:
        flags['no_fav_song'] = True
    elif cur_singer_ent is None:
        song_slots = NameFavoriteSongTemplate().execute(utterance)
        if song_slots is not None and 'favorite' in song_slots:
            cur_song_str = song_slots['favorite']
            cur_song_ent = rg.get_song_entity(cur_song_str)

            if cur_song_ent:
                tils = get_til_title(cur_song_ent.name)
                if len(tils):
                    flags['tils_exist'] = True

            metadata = rg.get_song_meta(cur_song_str, None)
            if metadata:
                flags['metadata_exists'] = True
                cur_singer_str = metadata['artist']

    if cur_song_str is not None:
        state.cur_song_str = cur_song_str
    if cur_song_ent is not None:
        state.cur_song_ent = cur_song_ent
    if cur_singer_str is not None:
        state.cur_singer_str = cur_singer_str

    return flags

def prompt_nlu_processing(rg, state, utterance, response_types):
    flags = {
        'tils_exist': False,
        'cur_song_ent_exists': False,
        'metadata_exists': False
    }

    cur_song_ent, cur_singer_ent = rg.get_song_and_singer_entity()
    if cur_song_ent:
        cur_song_str = cur_song_ent.talkable_name
        cur_song_str = re.sub(r'\(.*?\)', '', cur_song_str)
        flags['cur_song_ent_exists'] = True
        cur_singer_str = None
        if cur_singer_ent:
            cur_singer_str = cur_singer_ent.talkable_name
            cur_singer_str = re.sub(r'\(.*?\)', '', cur_singer_str)

        tils = get_til_title(cur_song_ent.name)
        if len(tils):
            flags['tils_exist'] = True
        else:
            metadata = rg.get_song_meta(cur_song_str, cur_singer_str)
            if metadata:
                flags['metadata_exists'] = True
                cur_singer_str = metadata['artist'] 

        if cur_song_str is not None:
            state.cur_song_str = cur_song_str
        if cur_song_ent is not None:
            state.cur_song_ent = cur_song_ent
        if cur_singer_str is not None:
            state.cur_singer_str = cur_singer_str

    return flags









