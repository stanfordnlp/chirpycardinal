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

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'thats': False,
		'no': False,
		'did_not_know': False,
		'response': '',
		'metadata': None,
		'cur_song_str': '',
		'cur_singer_str': ''
	}

	entity = get_music_entity(rg)

	if ResponseType.NO in response_types or ResponseType.NEGATIVE in response_types:
		flags['no'] = True
	else:
		if ResponseType.THATS in response_types and state.just_used_til::
			flags['thats'] = True
			flags['response'] = rg.state_manager.current_state.choose_least_repetitive(RESPONSE_TO_THATS)
		elif ResponseType.DIDNT_KNOW in response_types and state.just_used_til:
			flags['did_not_know'] = True
			flags['response'] = rg.state_manager.current_state.choose_least_repetitive(RESPONSE_TO_DIDNT_KNOW)

		flags['metadata'] = rg.get_song_meta(state.cur_song_str, state.cur_singer_str)
		flags['cur_song_str'] = state.cur_song_str
		flags['cur_singer_str'] = state.cur_singer_str

	return flags
