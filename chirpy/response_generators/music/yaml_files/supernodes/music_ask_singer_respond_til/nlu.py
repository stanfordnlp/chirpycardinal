from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.music_helpers import ResponseType


def nlu_processing(rg, state, utterance, response_types):
    flags = {
        'has_next_song': False,
        'comment_on_singer_only': False
    }

    cur_singer_str = rg.state.cur_singer_str
    top_songs = rg.get_songs_by_musician(cur_singer_str)
    next_song = None
    for next_song in top_songs:
        if next_song != cur_song_str:
            break
    if next_song:
        flags['has_next_song'] = True
        flags['next_song'] = next_song
    else:
        flags['comment_on_singer_only'] = True

    flags['cur_singer_str'] = cur_singer_str

    return flags



