from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.music_helpers import ResponseType


def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'thats': False,
		'didnt_know': False,
		'answered_no': False,
		'answered_yes': False,
		'questioned': False,
		'opinion': False,
		'only_til': False,
		'cur_singer_str': '',
		'cur_singer_ent': None,
		'rg': None
	}

	if ResponseType.THATS in response_types and state.just_used_til:
		flags['thats'] = True
	elif ResponseType.DIDNT_KNOW in response_types and state.just_used_til:
		flags['didnt_know'] = True
	elif ResponseType.NEGATIVE in response_types or \
             ResponseType.NO in response_types or \
             ResponseType.DONT_KNOW in response_types:
        flags['answered_no'] = True
    elif ResponseType.POSITIVE in response_types or ResponseType.YES in response_types:
    	flags['answered_yes'] = True
    elif ResponseType.QUESTION in response_types:
    	flags['questioned'] = True
    elif ResponseType.OPINION in response_types:
    	flags['opinion'] = True
    elif state.just_used_til:
    	flags['only_til'] = True

    flags['cur_singer_ent'] = rg.state.cur_singer_ent
    flags['cur_singer_str'] = rg.state.cur_singer_str

    top_songs = rg.get_songs_by_musician(flags['cur_singer_str'])
    cur_song_str = None
    cur_song_ent = None
    if top_songs: cur_song_str = top_songs[0]
    if cur_song_str:
        cur_song_ent = rg.get_song_entity(cur_song_str)
    flags['cur_song_str'] = cur_song_str
    flags['cur_song_ent'] = cur_song_ent

    flags['rg'] = rg

    return flags



