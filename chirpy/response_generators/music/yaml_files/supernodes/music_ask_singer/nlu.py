import logging
import random
import re

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.response_generators.music.state import ConditionalState
from chirpy.response_generators.wiki2.wiki_utils import get_til_title

def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'til_exists': False
    }

    cur_song_str = rg.state.cur_song_str
    cur_singer_str = rg.state.cur_singer_str
    cur_singer_ent = rg.state.cur_singer_ent

    if cur_singer_str is None and cur_song_str is not None:
        metadata = rg.get_song_meta(cur_song_str)
        cur_singer_str = metadata['artist']
    if cur_singer_str:
        cur_singer_ent = rg.get_musician_entity(cur_singer_str)
    if cur_singer_ent:
    	tils = get_til_title(cur_singer_ent.name)
    	if len(tils):
    		flags['til_exists'] = True
    		flags['tils'] = tils


    return flags



