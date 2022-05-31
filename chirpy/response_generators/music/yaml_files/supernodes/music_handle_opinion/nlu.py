import random

from chirpy.response_generators.music.music_helpers import ResponseType

def nlu_processing(rg, state, utterance, response_types):
	# flags is recommended to contain prompt_treelet as a key
	flags = {
		'listens_frequently': False,
		'listens_everday': False,
		'does_not_listen': False,
		'unsure_about_music': False,
		'likes_music': False,
		'catch_all': False
	}
	if ResponseType.FREQ in response_types:
		if 'everyday' in utterance:
			flags['listens_everday'] = True
			# flags['listens_everday'] = 'Well for me, I love listening to music everyday too!'
		else:
			flags['listens_frequently'] = True
			# flags['freq_prefix'] = 'Well for me, I love listening to music everyday!'
	elif (ResponseType.NO in response_types or ResponseType.NEGATIVE in response_types) and not ResponseType.DONT_KNOW in response_types:
		flags['does_not_listen'] = True
	elif ResponseType.DONT_KNOW in response_types:
		flags['unsure_about_music'] = True
	elif ResponseType.YES in response_types or ResponseType.POSITIVE in response_types or ResponseType.MUSIC_RESPONSE in response_types:
		flags['likes_music'] = True
	else:
		flags['catch_all'] = True

	return flags

def prompt_nlu_processing(rg, state, utterance, response_types):
	flags = {
		'have_prompted': False,
		'user_mentioned_music_positive': False
	}
	flags['have_prompted'] = state.have_prompted
	if ResponseType.MUSIC_KEYWORD in response_types and \
		   ResponseType.POSITIVE in response_types:
		flags['user_mentioned_music_positive'] = True
	return flags

