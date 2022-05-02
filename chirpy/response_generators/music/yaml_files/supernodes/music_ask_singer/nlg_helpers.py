import random
import re

def process_til(til):
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