import random
import re

from chirpy.response_generators.music.utils import WikiEntityInterface
from chirpy.response_generators.wiki2.wiki_utils import get_til_title
from chirpy.response_generators.music.expression_lists import process_til
from chirpy.core.response_generator import nlg_helper

@nlg_helper
def get_til_response(tils):
	til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
	return process_til(til)

@nlg_helper
def get_til_title_helper(title):
	return get_til_title(title)
