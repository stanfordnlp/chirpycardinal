import random
import re

from chirpy.core.response_generator import nlg_helper
from chirpy.response_generators.wiki2.wiki_utils import get_til_title

import chirpy.response_generators.music.response_templates.general_templates as templates

@nlg_helper
def least_repetitive_compliment(rg):
	return rg.state_manager.current_state.choose_least_repetitive(templates.compliment_user_song_choice())

@nlg_helper
def pick_til(cur_song_ent):
	tils = get_til_title(cur_song_ent.name)
	til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
	return templates.til(til)

@nlg_helper
def singer_comment(singer_name):
	return random.choice([f'{singer_name} does really nice songs right?', f'{singer_name} has some really good tunes right?'])