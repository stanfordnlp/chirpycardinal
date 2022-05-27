import random
import re

from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
import chirpy.response_generators.music.response_templates.general_templates as templates
from chirpy.core.response_generator import nlg_helper

def choose(rg, items):
    return rg.state_manager.current_state.choose_least_repetitive(items)

@nlg_helper
def cur_song_ent_exists_response(rg):
    return choose(rg, templates.compliment_user_song_choice())

@nlg_helper
def song_slots_exists_response(rg):
    return choose(rg, templates.compliment_user_song_choice())

@nlg_helper
def thats_response(rg):
    return choose(rg, RESPONSE_TO_THATS)

@nlg_helper
def didnt_know_response(rg):
    return choose(rg, RESPONSE_TO_DIDNT_KNOW)

def no_response(rg):
    return choose(rg, [ 'It\'s okay!', 'Don\'t worry about it!' ])

def yes_response(rg):
    return choose(rg, [ 'I know, right?', "It's great that you do!"])

def question_response(rg):
    return choose(rg, [
                'Oh I\'m not too sure about that.',
                'Ah I\'m not sure, I\'ll need to check about that.',
                'Oh hmm, I\'m not too sure about that.',
                'Oh dear I don\'t know, I\'ll need to find out.',
        ])

def opinion_response(rg):
    return choose(rg, [
                'Yeah I totally agree with that!',
                'Me too!',
                'Absolutely!',
        ])

def til_response(rg):
    return choose(rg, [
                'I thought that was an interesting tidbit!',
                'I hope you found that interesting!',
        ])

def catch_all_response(rg):
    return choose(rg, [ 'That\'s great!', 'Awesome!', 'Cool!'])
