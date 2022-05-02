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
		'instr_exists_with_til': False,
		'instr_exists_wo_til': False,
		'tils': None,
		'entity_name': '',
		'no_fav_instrument': False,
		'catch_all': False
		'prompt_treelet': ''
	}

	entity = get_music_entity(rg)

	if entity:
		tils = get_til_title(entity.name)
		flags['entity_name'] = entity.name
		if len(tils):
			flags['tils'] = tils
			flags['instr_exists_with_til'] = True
		else:
			flags['instr_exists_wo_til'] = True
	elif any(i in response_types for i in [ ResponseType.NO, ResponseType.DONT_KNOW, ResponseType.NOTHING]):
		flags['no_fav_instrument'] = True
	else:
		flags['catch_all'] = True

	if not flags['instr_exists_with_til']:
		flags['prompt_treelet'] = random.choice(['music_get_singer', 'music_get_song'])

	return flags

def get_music_entity(rg):
        def is_instrument(ent):
            return ent and WikiEntityInterface.is_in_entity_group(ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_instrument)
        cur_entity = rg.get_current_entity()
        entity_linker_results = rg.state_manager.current_state.entity_linker
        entities = []
        if cur_entity: entities.append(cur_entity)
        if len(entity_linker_results.high_prec): entities.append(entity_linker_results.high_prec[0].top_ent)
        if len(entity_linker_results.threshold_removed): entities.append(entity_linker_results.threshold_removed[0].top_ent)
        if len(entity_linker_results.conflict_removed): entities.append(entity_linker_results.conflict_removed[0].top_ent)
        for e in entities:
            if is_instrument(e): return e