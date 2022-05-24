from chirpy.response_generators.music.music_helpers import ResponseType

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'intro': True
	}

	return flags

def prompt_nlu_processing(rg, state, utterance, response_types):
	flags = {
		'have_prompted': False,
		'user_mentioned_music': False,
		'generic_prompt': False
	}

	flags['have_prompted'] = state.have_prompted
	if ResponseType.MUSIC_KEYWORD in response_types and not ResponseType.POSITIVE in response_types:
		flags['user_mentioned_music'] = True
	else:
		flags['generic_prompt'] = True
	return flags
