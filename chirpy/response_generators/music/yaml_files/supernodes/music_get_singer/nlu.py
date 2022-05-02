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

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'singer_ent_exists': False,
		'is_musical_group': False,
		'no_genre': False,
		'singer_str': '',
		'tils': None,
		'tils_exist': False,
		'no_fav_musician': False,
		'catch_all': False

	}

	cur_singer_ent = get_music_entity(rg)
	flags['response'] = rg.state_manager.current_state.choose_least_repetitive(templates.compliment_user_musician_choice())
	
	parsed_musician_from_utterance = False
	if cur_singer_ent is None:
		slots = NameFavoriteSongTemplate().execute(utterance)
		if slots is not None and 'favorite' in slots:
			flags['singer_str'] = slots['favorite']
			cur_singer_ent = rg.get_song_entity(flags['singer_str'])
			flags['singer_str_exists'] = True
			if rg.get_singer_genre(flags['singer_str']) is None:
				flags['no_genre'] = True
	else:
		flags['singer_str'] = re.sub(r'\(.*?\)', '', cur_singer_ent.talkable_name)

	if cur_singer_ent:
		flags['singer_ent_exists'] = True
		if WikiEntityInterface.is_in_entity_group(cur_singer_ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_group):
			flags['is_musical_group'] = True
		tils = get_til_title(cur_singer_ent.name)
		if len(tils):
			flags['tils'] = tils
			flags['tils_exist'] = True
	elif any(i in response_types for i in [ ResponseType.NO, ResponseType.DONT_KNOW, ResponseType.NOTHING, ResponseType.NEGATIVE]):
		flags['no_fav_musician'] = True
	else:
		flags['catch_all'] = True

	return flags

def get_music_entity(rg):
    def is_singer(ent):
        return ent and WikiEntityInterface.is_in_entity_group(ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musician)
    cur_entity = rg.get_current_entity()
    entity_linker_results = rg.state_manager.current_state.entity_linker
    entities = []
    if cur_entity: entities.append(cur_entity)
    if len(entity_linker_results.high_prec): entities.append(entity_linker_results.high_prec[0].top_ent)
    if len(entity_linker_results.threshold_removed): entities.append(entity_linker_results.threshold_removed[0].top_ent)
    if len(entity_linker_results.conflict_removed): entities.append(entity_linker_results.conflict_removed[0].top_ent)
    for e in entities:
        if is_singer(e): return e