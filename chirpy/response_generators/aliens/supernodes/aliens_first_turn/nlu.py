from chirpy.response_generators.music.music_helpers import ResponseType

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'user_not_interested': False,
		'user_interested': False,
		'neutral': False
	}

	if ResponseType.NO in response_types or ResponseType.DISINTERESTED in response_types:
		flags['user_not_interested'] = True
	elif ResponseType.QUESTION in response_types:
		flags['handle_q'] = True
	elif ResponseType.YES in response_types:
		flags['user_interested'] = True
	else:
		flags['neutral'] = True

	return flags