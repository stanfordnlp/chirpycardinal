from chirpy.response_generators.music.music_helpers import ResponseType

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'has_opinion': False
	}

	if ResponseType.NO in response_types or ResponseType.DISINTERESTED in response_types:
		flags['user_not_interested'] = True
	elif ResponseType.QUESTION in response_types:
		flags['handle_q'] = True
	elif ResponseType.OPINION in response_types:
		flags['has_opinion'] = True
	return flags