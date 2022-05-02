import logging
import random
import re

from chirpy.core.response_generator import Treelet
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.music.regex_templates.name_favorite_song_template import NameFavoriteSongTemplate
from chirpy.response_generators.music.utils import WikiEntityInterface
from chirpy.response_generators.wiki2.wiki_utils import get_til_title
import chirpy.response_generators.music.response_templates.general_templates as templates
from chirpy.response_generators.music.state import ConditionalState
from chirpy.response_generators.music.music_helpers import ResponseType

def nlu_processing(rg, state, utterance, response_types):
	flags = {
		'song_ent_exists': False,
		'singer_ent_exists': False,
		'dont_know': False,
		'no_fav_song': False,
		'tils': None,
		'tils_exist': False,
		'cur_song_str': '',
		'cur_song_str_exists': False,
		'no_metadata': False,
		'metadata': None
	}

	cur_song_ent, cur_singer_ent = get_music_entity(rg)
	flags['response'] = rg.state_manager.current_state.choose_least_repetitive(templates.compliment_user_song_choice())
	cur_song_str = ''
	if cur_song_ent:
		flags['song_ent_exists'] = True
		cur_song_str = cur_song_ent.talkable_name
	if cur_singer_ent:
		flags['singer_ent_exists'] = True
	if not flags['song_ent_exists'] and not flags['singer_ent_exists']:
		if ResponseType.DONT_KNOW in response_types:
			flags['dont_know'] = True
		elif ResponseType.NO in response_types or ResponseType.NOTHING in response_types:
			flags['no_fav_song'] = True
		else:
			song_slots = NameFavoriteSongTemplate().execute(utterance)
			if song_slots is not None and 'favorite' in song_slots:
				cur_song_str = song_slots['favorite']
				flags['cur_song_str_exists'] = True
				flags['response'], metadata = comment_song(rg, cur_song_str, response=flags['response'])
				if metadata is None:
					flags['no_metadata'] = True
				else:
					flags['metadata'] = metadata
					flags['no_metadata'] = False

				cur_song_ent = rg.get_song_entity(cur_song_str)

	if cur_song_ent:
		tils = get_til_title(cur_song_ent.name)
		if len(tils):
			flags['tils'] = tils
			flags['tils_exist'] = True
		else:
			cur_song_str = re.sub(r'\(.*?\)', '', cur_song_ent.talkable_name)
			if flags['singer_ent_exists']:
				metadata = rg.get_song_meta(cur_song_str, cur_singer_ent.talkable_name)
			else:
				metadata = rg.get_song_meta(cur_song_str, None)
			if metadata is None:
				flags['no_metadata'] = True
			else:
				flags['metadata'] = metadata
				flags['no_metadata'] = False

	flags['cur_song_str'] = cur_song_str

	return flags

def get_music_entity(rg):
    def is_song(ent):
        return ent and WikiEntityInterface.is_in_entity_group(ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musical_work)
    def is_singer(ent):
        return ent and WikiEntityInterface.is_in_entity_group(ent, ENTITY_GROUPS_FOR_EXPECTED_TYPE.musician)
    cur_entity = rg.get_current_entity()
    entity_linker_results = rg.state_manager.current_state.entity_linker
    song, singer = None, None
    entities = []
    if cur_entity: entities.append(cur_entity)
    if len(entity_linker_results.high_prec): entities.append(entity_linker_results.high_prec[0].top_ent)
    if len(entity_linker_results.threshold_removed): entities.append(entity_linker_results.threshold_removed[0].top_ent)
    if len(entity_linker_results.conflict_removed): entities.append(entity_linker_results.conflict_removed[0].top_ent)
    for e in entities:
        if is_song(e) and song is None: song = e
        elif is_singer(e) and singer is None: singer = e
    return song, singer

def comment_song(rg, song_name, singer_name=None, response=None):
	"""
    Make a relevant comment about the song
    and end with a followup question.
    """
    metadata = rg.get_song_meta(song_name, singer_name)
    if metadata:
        comment = random.choice([
            f'Oh yeah, {metadata["song"]} is a song by {metadata["artist"]} released in {metadata["year"]} right?',
            f'{metadata["song"]} was released by {metadata["artist"]} in {metadata["year"]} right?',
        ])
        if response is None: response = comment
        else: response = f'{response} {comment}'
    else:
        response = None
    return response, metadata

