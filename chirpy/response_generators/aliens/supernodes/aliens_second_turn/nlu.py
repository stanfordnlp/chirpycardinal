from chirpy.response_generators.music.music_helpers import ResponseType

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'user_said_yes': False
	}

	if ResponseType.YES in response_types:
		flags['user_said_yes'] = True
	return flags