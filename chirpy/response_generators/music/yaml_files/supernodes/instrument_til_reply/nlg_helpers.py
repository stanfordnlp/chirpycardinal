from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.core.response_generator import nlg_helper

@nlg_helper
def get_responses_to_thats():
	return RESPONSE_TO_THATS

@nlg_helper
def get_responses_to_didnt_know():
	return RESPONSE_TO_DIDNT_KNOW
