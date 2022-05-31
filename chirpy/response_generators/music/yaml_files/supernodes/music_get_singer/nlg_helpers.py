import random
import re

from chirpy.core.response_generator import nlg_helper

import chirpy.response_generators.music.response_templates.general_templates as templates
from chirpy.response_generators.wiki2.wiki_utils import get_til_title
from chirpy.response_generators.music.regex_templates import NameFavoriteSongTemplate

@nlg_helper
def pick_til(tils):
	til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
	return templates.til(til)

@nlg_helper
def singer_comment(singer_name):
	return random.choice([f'{singer_name} does really nice songs right?', f'{singer_name} has some really good tunes right?'])

@nlg_helper
def least_repetitive_compliment(rg):
	return rg.state_manager.current_state.choose_least_repetitive(templates.compliment_user_musician_choice())

@nlg_helper
def get_singer_str(rg):
	singer_str = ''
	cur_singer_ent = rg.get_singer_entity()
	if cur_singer_ent is None:
		slots = NameFavoriteSongTemplate().execute(rg.utterance)
		if slots is not None and 'favorite' in slots:
			singer_str = slots['favorite']
			temp = rg.get_song_entity(singer_str)
			if temp:
				singer_str = temp.name
	else:
		singer_str = re.sub(r'\(.*?\)', '', cur_singer_ent.talkable_name)
	return singer_str

@nlg_helper
def singer_parsed_ent(rg):
	cur_singer_ent = rg.get_singer_entity()
	if cur_singer_ent is None:
		slots = NameFavoriteSongTemplate().execute(rg.utterance)
		if slots is not None and 'favorite' in slots:
			singer_str = slots['favorite']
			cur_singer_ent = rg.get_song_entity(singer_str)
	return cur_singer_ent

@nlg_helper
def get_talkable_singer_name(singer_ent):
	cur_singer_str = singer_ent.talkable_name
	cur_singer_str = re.sub(r'\(.*?\)', '', cur_singer_str)
	return cur_singer_str

@nlg_helper
def get_tils(singer_name):
	return get_til_title(singer_name)

@nlg_helper
def comment_singer(rg, singer_name):
    """
    Make a relevant comment about the singer and returns (comment, genre)
    """
    genre = rg.get_singer_genre(singer_name)
    if genre:
        return rg.state_manager.current_state.choose_least_repetitive([
            f'{singer_name} does really fabulous {genre} songs right?',
            f'The {genre} songs by {singer_name} are really good right?',
        ]), genre
    return rg.state_manager.current_state.choose_least_repetitive([
        f'{singer_name} does really nice songs right?',
        f'{singer_name} has some really good tunes right?',
    ]), genre
