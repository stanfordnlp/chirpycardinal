import random
import re

from chirpy.core.response_generator import nlg_helper
from chirpy.response_generators.wiki2.wiki_utils import get_til_title

@nlg_helper
def process_til(singer_name):
    tils = get_til_title(singer_name)
    til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
    return random.choice([
        f'I found out that {til}. Isn\'t that interesting?',
        f'I learned that {til}. What do you think about that?',
        f'Did you know that {til}?',
        f'I just found out the other day that {til}. Isn\'t that fascinating? What do you think?',
    ])


def get_til_response(tils):
    til = re.sub(r'\(.*?\)', '', random.choice(tils)[0])
    response = process_til(til)
    return response