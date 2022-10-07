from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.music_helpers import ResponseType


def response_nlu_processing(rg, state, utterance, response_types):
	response_flags = {
		'thats': False,
		'didnt_know': False,
		'answered_no': False,
		'answered_yes': False,
		'questioned': False,
		'opinion': False,
		'just_used_til_only': False
	}

	if ResponseType.THATS in response_types and state.just_used_til:
		response_flags['thats'] = True
	elif ResponseType.DIDNT_KNOW in response_types and state.just_used_til:
		response_flags['didnt_know'] = True
	elif ResponseType.NEGATIVE in response_types or \
			 ResponseType.NO in response_types or \
			 ResponseType.DONT_KNOW in response_types:
		response_flags['answered_no'] = True
	elif ResponseType.POSITIVE in response_types or ResponseType.YES in response_types:
		response_flags['answered_yes'] = True
	elif ResponseType.QUESTION in response_types:
		response_flags['questioned'] = True
	elif ResponseType.OPINION in response_types:
		response_flags['opinion'] = True
	elif state.just_used_til:
		response_flags['just_used_til_only'] = True

	return response_flags



