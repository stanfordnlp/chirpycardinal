from chirpy.core.response_generator import nlg_helper
import random

@nlg_helper
def choose_random(s1, s2):
	return random.choice([s1, s2])