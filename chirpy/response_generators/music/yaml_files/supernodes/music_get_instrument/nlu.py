from chirpy.response_generators.wiki2.wiki_utils import get_til_title
from chirpy.response_generators.music.music_helpers import ResponseType

def response_nlu_processing(rg, state, utterance, response_types):
	response_flags = {
		'instr_exists_with_til': False,
		'instr_exists_wo_til': False,
		'no_fav_instrument': False,
		'catch_all': False
	}

	entity = rg.get_instrument_entity()

	if entity:
		tils = get_til_title(entity.name)
		if len(tils):
			response_flags['instr_exists_with_til'] = True
		else:
			response_flags['instr_exists_wo_til'] = True
	elif any(i in response_types for i in [ ResponseType.NO, ResponseType.DONT_KNOW, ResponseType.NOTHING]):
		response_flags['no_fav_instrument'] = True
	else:
		response_flags['catch_all'] = True

	return response_flags

def prompt_nlu_processing(rg, state, utterance, response_types):
	flags = {
		'use_til': False,
		'generic': False
	}
	entity = rg.get_instrument_entity()
	if entity:
		tils = get_til_title(entity.name)
		if len(tils):
			flags['use_til'] = True
		else:
			flags['generic'] = True
	return flags


