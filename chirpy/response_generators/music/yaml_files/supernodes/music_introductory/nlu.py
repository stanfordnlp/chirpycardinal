from chirpy.response_generators.music.music_helpers import ResponseType

def response_nlu_processing(rg, state, utterance, response_types):
	response_flags = {'intro': True}

	return response_flags

def prompt_nlu_processing(rg, state, utterance, response_types):		# TODO: Check this
	prompt_flags = {
		'have_prompted': False,
		'user_mentioned_music': False,
		'generic_prompt': False
	}

	prompt_flags['have_prompted'] = state.have_prompted
	if ResponseType.MUSIC_KEYWORD in response_types and not ResponseType.POSITIVE in response_types:
		prompt_flags['user_mentioned_music'] = True
	else:
		prompt_flags['generic_prompt'] = True
	return prompt_flags
