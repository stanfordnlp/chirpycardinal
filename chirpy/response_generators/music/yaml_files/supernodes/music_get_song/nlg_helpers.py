import random
import re

import chirpy.response_generators.music.response_templates.general_templates as templates

def pick_til(tils):
	til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
	return templates.til(til)

def singer_comment(singer_name):
	return random.choice([f'{singer_name} does really nice songs right?', f'{singer_name} has some really good tunes right?'])