from chirpy.core.response_generator import Treelet, nlg_helper
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW

## nlg_helper — chirpy.core.response_generator

def choose(rg, items):
	return rg.state_manager.current_state.choose_least_repetitive(items)

@nlg_helper
def get_cur_song_str(rg):
    cur_song_str = None
    top_songs = rg.get_songs_by_musician(rg.state.cur_singer_str)
    if top_songs: cur_song_str = top_songs[0]
    return cur_song_str

@nlg_helper
def complement_fav_song(rg, cur_singer_str, cur_song_str):
    if cur_song_str:
        return choose(rg, [
            f'As a fan of {cur_singer_str}, I must say that my favorite song is {cur_song_str}. Do you like that too?',
            f'Oh I really love {cur_song_str} by {cur_singer_str}! How about you? Do you like it as well?',
        ])
    else:
        return f'{cur_singer_str} seems to be really talented! Do you like any other songs by {cur_singer_str}?'

@nlg_helper
def thats_response(rg):
	return choose(rg, RESPONSE_TO_THATS)

@nlg_helper
def didnt_know_response(rg):
	return choose(rg, RESPONSE_TO_DIDNT_KNOW)

@nlg_helper
def no_response(rg):
	return choose(rg, [ 'It\'s okay!', 'Don\'t worry about it!'])

@nlg_helper
def yes_response(rg):
	return choose(rg, [ 'I know, right?', "It's great that you do!"])

@nlg_helper
def question_response(rg):
	return choose(rg, [ 'Oh I\'m not too sure about that.', 'Ah I\'m not sure, I\'ll need to check about that.', 'Oh hmm, I\'m not too sure about that.', 'Oh dear I don\'t know, I\'ll need to find out.'])

@nlg_helper
def opinion_response(rg):
	return choose(rg, [
                'Yeah I totally agree with that!',
                'Me too!',
                'Absolutely!',
            ])

@nlg_helper
def til_only_response(rg):
	return choose(rg, [ 'I thought that was an interesting tidbit!', 'I hope you found that interesting!'])

@nlg_helper
def talk_about_top_songs(rg, cur_singer_str, cur_song_str=None):
    top_songs = rg.get_songs_by_musician(cur_singer_str)
    if top_songs: cur_song_str = top_songs[0]
    if cur_song_str:
        cur_song_ent = rg.get_song_entity(cur_song_str)
        response = choose(rg, [
            f'As a fan of {cur_singer_str}, I must say that my favorite song is {cur_song_str}. Do you like that too?',
            f'Oh I really love {cur_song_str} by {cur_singer_str}! How about you? Do you like it as well?',
        ])
    else:
        response = f'{cur_singer_str} seems to be really talented! Do you like any other songs by {cur_singer_str}?'

    return response
