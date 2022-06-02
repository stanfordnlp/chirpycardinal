from chirpy.response_generators.music.music_helpers import ResponseType

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'has_opinion': False
	}

	if ResponseType.OPINION in response_types:
		flags['has_opinion'] = True
	return flags