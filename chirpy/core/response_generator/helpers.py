"""
Helper functions that are used by both ResponseGenerator and Treelet
"""
from functools import partial, update_wrapper
from collections import defaultdict
import re
import inspect
from typing import Tuple
from chirpy.core.regex.word_lists import CUTOFF
from chirpy.core.regex import response_lists

from chirpy.core.regex.templates import (
    ClarifyingPhraseTemplate,
    AbilitiesQuestionTemplate,
    PersonalWhQuestionTemplate,
    InterruptionQuestionTemplate,
    NeverMindTemplate,
    RequestPlayTemplate,
    NotRequestPlayTemplate,
    ChattyTemplate,
    MyNameIsNonContextualTemplate,
    MyNameIsNotTemplate,
    SayThatAgainTemplate,
    RequestNameTemplate,
    RequestStoryTemplate,
    ComplimentTemplate,
    RequestAgeTemplate,
    ComplaintMisheardTemplate,
    ComplaintClarificationTemplate,
    ComplaintPrivacyTemplate,
    ComplaintRepetitionTemplate,
    WeatherTemplate,
    WhatTimeIsItTemplate,
    CutOffTemplate,
    DontKnowTemplate
)
from chirpy.response_generators.personal_issues.regex_templates import PersonalSharingTemplate
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION
# from chirpy.response_generators.alexa_commands.regex_templates import AlexaCommandTemplate # TODO: refactor this; rn it depends on a bunch of resource files
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.util import load_text_file, contains_phrase

import logging
logger = logging.getLogger('chirpylogger')

COMPLAINT_THRESHOLD = 0.91
FP_TO_SP = {"am" : "are", "are" : "am", 'i' : 'you', 'my' : 'yours', 'me' : 'you', 'mine' : 'yours', 'you' : 'I', 'your' : 'my', 'yours' : 'mine'}
SP_TO_FP = {v: k for k, v in FP_TO_SP.items()}
CONFIRM_SAYING_PHRASES = [
    "Yes, that's what I said",
    "Yeah, that's right",
    "Yep",
    "Yeah",
    "That's right"
]
CORRECT_SAYING_PHRASES = [
    "No, I said",
    "Actually, I said",
    "Oh, sorry, I meant",
    "Oops, I actually said"
]
THANK_INQUIRY_PHRASES = [
    "Thanks for asking!",
    "I'm glad you asked."
]

OFF_TOPIC_PHRASES = [
    "Sorry, I must've heard something else. I heard",
    "Sorry, I thought you said",
    "Oops, I must've misheard you. I thought I heard"
]

GOT_FACT_CHECKED_PHRASES = [
    "Oops,",
    "Hmm, I think you might be right"
]

REPETITION_APOLOGY = [
    "Sorry. Let me say that again.",
    "Oh, sorry. Let me try again.",
    "Sure.",
    'Sure let me say that again.',
    'Oops, let me repeat that.',
    'Oh, this is what I meant to say.',
]

SORRY_FOR_CONNECTION = [
    "I'm so sorry. It seems like we have some miscommunication. Let's move on, shall we?",
    "I'm sorry. Looks like we have some miscommunication. Let's move on.",
    "Sorry. Seems like we have some miscommunication.",
]

BOT_REPEAT_PHRASES = CONFIRM_SAYING_PHRASES + CORRECT_SAYING_PHRASES + REPETITION_APOLOGY + response_lists.CLARIFICATION_COMPLAINT_RESPONSE

USER_REPEAT_PHRASES = response_lists.MISHEARD_COMPLAINT_RESPONSE + response_lists.CUTOFF_USER_RESPONSE

DEFAULT_SENTINEL = "default-sentinel"

import os
STOPWORDS_FILEPATH = os.path.join(os.path.dirname(__file__), '../../data/long_stopwords.txt')
STOPWORDS = load_text_file(STOPWORDS_FILEPATH)

global_nlg_helpers_cache = defaultdict(lambda: {})
def nlg_helper(func):
    supernode_path = inspect.getfile(func)# get path to current rg+supernode, i.e. "MUSIC/music_ask_song"
    components = supernode_path.split('/')
    ind = -1
    for i in range(len(components)):
        if components[i] == 'supernodes':
            ind = i
            break
    supernode_name = components[ind+1]
    if func.__name__ in global_nlg_helpers_cache[supernode_name]:
        raise KeyError(f'Duplicate function name {func.__name__} found in cache for {supernode_name}')
    global_nlg_helpers_cache[supernode_name][func.__name__] = func
    return func
    
def nlg_helper_augmented(func):
    supernode_path = inspect.getfile(func)# get path to current rg+supernode, i.e. "MUSIC/music_ask_song"
    components = supernode_path.split('/')
    ind = -1
    for i in range(len(components)):
        if components[i] == 'supernodes':
            ind = i
            break
    supernode_name = components[ind+1]
    if func.__name__ in global_nlg_helpers_cache[supernode_name]:
        raise KeyError(f'Duplicate function name {func.__name__} found in cache for {supernode_name}')
        
    def modified_func(*args, **kwargs):
        print("calling modified_func with", args, kwargs, "globals are", globals().keys(), "locals are", locals().keys())
        return func(*args, **kwargs)
    global_nlg_helpers_cache[supernode_name][func.__name__] = modified_func
    return func

def get_context_for_supernode(supernode):
    # context = GLOBAL_CONTEXT -- do this once we have actual global context
    context = {}
    context.update(global_nlg_helpers_cache[supernode])
    return context



def wrapped_partial(func, *args, **kwargs):
    partial_func = partial(func, *args, **kwargs)
    update_wrapper(partial_func, func)
    return partial_func

def first_to_second_person(response) -> str:
    result = ' '.join([FP_TO_SP.get(word, word) for word in response.split()])
    return result

def second_to_first_person(response) -> str:
    result = ' '.join([SP_TO_FP.get(word, word) for word in response.split()])
    return result


def construct_response_types_tuple(response_types) -> Tuple:
    return tuple([x.name for x in response_types])

def get_last_sentence(utterance, drop_punctuation=True, split_clauses=False):
    punctuation_str = ".?!"
    if split_clauses:
        punctuation_str += ";:,"
    if drop_punctuation:
        sentence_split_regex = r"[" + re.escape(punctuation_str) + r"]"
    else:
        sentence_split_regex = r"(?<=[" + re.escape(punctuation_str) + r"])\s"
    last_sentence = list(filter(None, re.split(sentence_split_regex, utterance)))[-1]
    return last_sentence

def user_said_chatty_phrase(state_manager):
    state = state_manager.current_state
    utterance = state.text
    nav_intent_output = state.navigational_intent
    chatty_slots = ChattyTemplate().execute(utterance)
    if chatty_slots: return chatty_slots

    # if didn't match chatty_slots, but still should respond w/ a default chatty-phrase response:
    # TODO: this is hacky AF.
    # this should be handled by the chatty abrupt handlers alreayd, enabling this can cause issues like:
    # the bot suggests something to talk about, the user says "sure let's talk about it", and the bot says "ok! what would you like to talk about?"
    # nontrivial_pos_intent = nav_intent_output.pos_intent and nav_intent_output.pos_topic is None
    # wants_more_info_on_topic = state_manager.last_state_active_rg in ['WIKI', 'NEWS'] and contains_phrase(utterance, {'tell'})
    # if nontrivial_pos_intent and not wants_more_info_on_topic:
    #     chatty_slots = {'chatty_phrase': DEFAULT_SENTINEL}
    return chatty_slots

def user_requested_repetition(state_manager) -> bool:
    """This method should classify whether the user's last utterance constituted a request for repetition.

    Positive examples:
    "I'm sorry?"
    "What was that?"
    "I didn't catch that."
    "[some phrase] what?"

    Negative examples:
    "I'm sorry to hear that."
    "I didn't catch anything on the fishing trip."

    Args:
        state (State): current state_manager state
    """
    state = state_manager.current_state
    utterance = state.text
    say_that_again_slots = SayThatAgainTemplate().execute(utterance)
    return say_that_again_slots


def user_requested_correction(state_manager):
    """This method should classify whether the user's last utterance constituted a request for correction (of user utterance).

    Positive examples:
    "That's not what I said"
    "No that's not it"
    "I didn't say [some phrase]"

    Args:
        state (State): current state_manager state
    """
    pass # currently in complaint RG


def user_requested_clarification(state_manager):
    """This method should classify whether the user's last utterance constituted a request for clarification (of bot response)
    that the bot can handle by repeating itself.

    Positive examples:
    "Wait, you said [phrase]?"
    "Excuse me, [something bot just mentioned]?"

    Args:
        state (State): current state_manager state
    """
    state = state_manager.current_state
    if len(state.history) < 1: return False # vacuous
    #if 'question' not in state.dialogact['top_1'] != 'question': return False # to request clarification, you have to ask a question UPDATE: turns out the classifier doesn't work for this situation
    user_utterance = state.text
    last_bot_utterance = state.history[-1]

    # template: CLARIFICATION PHRASE + OVERLAP WITH BOT = "yes, X is what I said"
    # CLARIFICATION PHRASE + NO OVERLAP WITH BOT = "actually, I said X"
    clarifier_slots = ClarifyingPhraseTemplate().execute(user_utterance)
    return clarifier_slots

def user_interrupted(state_manager) -> bool:
    state = state_manager.current_state
    user_utterance = state.text
    interruption_slots = InterruptionQuestionTemplate().execute(user_utterance)
    return interruption_slots

def user_asked_ablities_question(state_manager):
    """This method should classify whether the user's last utterance constituted a request for clarification (of bot response)

    Positive examples:
    "Can you listen to music?"
    "How did you go on a walk if you don't have legs?"

    Negative examples:
    "I want to know how you are"

    Args:
        state (State): current state_manager state
    """
    state = state_manager.current_state
    if len(state.history) < 1: return False # vacuous
    user_utterance = state.text

    # template: CLARIFICATION PHRASE + OVERLAP WITH BOT = "yes, X is what I said"
    # CLARIFICATION PHRASE + NO OVERLAP WITH BOT = "actually, I said X"
    ability_slots = AbilitiesQuestionTemplate().execute(user_utterance)
    return ability_slots

def user_asked_personal_question(state_manager):
    state = state_manager.current_state
    if len(state.history) < 1: return False
    user_utterance = state.text
    pq_slots = PersonalWhQuestionTemplate().execute(user_utterance)
    #logger.primary_info(f"Detected personal question slots: {pq_slots} for user_utterance {user_utterance}")
    if pq_slots: logger.primary_info(f"Detected personal question slots: {pq_slots}")
    return pq_slots


def user_requested_name(state_manager):
    state = state_manager.current_state
    utterance = state.text
    request_name_slots = RequestNameTemplate().execute(utterance)
    return request_name_slots

def is_game_or_music_request(state):
    utterance = state.text
    request_play_slots = RequestPlayTemplate().execute(utterance)
    not_request_play_slots = NotRequestPlayTemplate().execute(utterance)
    cur_entity = state.entity_tracker.cur_entity
    prev_bot_utt = state.history[-1] if len(state.history) >= 1 else ''
    did_not_ask_user_activity = "what do you like to do" not in prev_bot_utt.lower()
    found_musical_entity = False
    if state.entity_tracker.cur_entity_initiated_by_user_this_turn(state):
        for ent_group in [ENTITY_GROUPS_FOR_CLASSIFICATION.musician, ENTITY_GROUPS_FOR_CLASSIFICATION.musical_group,
                          ENTITY_GROUPS_FOR_CLASSIFICATION.musical_work]:
            if ent_group.matches(cur_entity):
                found_musical_entity = True
    return did_not_ask_user_activity and ((request_play_slots is not None and found_musical_entity) or
                        (request_play_slots is not None and not_request_play_slots is None))


def user_wants_name_correction(state_manager):
    state = state_manager.current_state
    utterance = state.text
    my_name_slots = MyNameIsNonContextualTemplate().execute(utterance)
    not_my_name_slots = MyNameIsNotTemplate().execute(utterance)
    if my_name_slots and state_manager.last_state_active_rg and state_manager.last_state_active_rg != 'LAUNCH':
        return my_name_slots
    if not_my_name_slots:
        return not_my_name_slots

# def user_said_alexa_command(state_manager):
#     state = state_manager.current_state
#     utterance = state.text
#     slots = AlexaCommandTemplate().execute(utterance)
#     return slots or is_game_or_music_request(state)

def user_gave_nevermind(state_manager):
    state = state_manager.current_state
    utterance = state.text
    slots = NeverMindTemplate().execute(utterance)
    return slots

def user_asked_for_story(state_manager):
    state = state_manager.current_state
    utterance = state.text
    request_story_slots = RequestStoryTemplate().execute(utterance)
    return request_story_slots

def user_shared_personal_problem(state_manager):
    utterance = state_manager.current_state.text
    return PersonalSharingTemplate().execute(utterance)

def user_said_anything(state_manager):
    """
    This should only kick in if previous response ends with
    "What would you like to talk about next?" and the user
    replies "anything" or IDK
    """
    if len(state_manager.current_state.history) == 0:
        return None
    previous_bot_utterance = state_manager.current_state.history[-1]
    utterance = state_manager.current_state.text
    nothing_replies = [
        "nothing",
        "anything",
        "whatever",
        "something else",
    ]
    triggers = [
        'talk about next?',
        'What are you interested in?',
        'like to know more about?',
        'what have you been interested in lately?',
        'like to learn more about?',
    ]
    if any(previous_bot_utterance.endswith(i) for i in triggers):
        if any(i in utterance for i in nothing_replies): return True
        if DontKnowTemplate().execute(utterance) is not None: return True
    return False


def user_gave_compliment(state_manager):
    state = state_manager.current_state
    utterance = state.text
    compliment_slots = ComplimentTemplate().execute(utterance)
    return compliment_slots

def user_got_cutoff(state_manager):
    state = state_manager.current_state
    utterance = state.text
    nav_intent_output = state.navigational_intent
    cutoff_slot = CutOffTemplate().execute(utterance)
    logger.primary_info(f"========={cutoff_slot}")
    # logger.primary_info(f"========={(nav_intent_output.pos_intent and nav_intent_output.pos_topic_is_hesitate and "depends on" not in utterance)}")
    return cutoff_slot or (nav_intent_output.pos_intent
            and nav_intent_output.pos_topic_is_hesitate
            and "depends on" not in utterance)
             # or (utterance in CUTOFF)

def user_asked_for_our_age(state_manager):
    state = state_manager.current_state
    utterance = state.text
    request_age_slots = RequestAgeTemplate().execute(utterance)
    return request_age_slots

def misheard_complaint(state_manager):
    state = state_manager.current_state
    utterance = state.text
    complaint_misheard_slots = ComplaintMisheardTemplate().execute(utterance)
    return complaint_misheard_slots

def unclear_complaint(state_manager):
    state = state_manager.current_state
    utterance = state.text
    clarification_slots = ComplaintClarificationTemplate().execute(utterance)
    had_confusion_word = ("confused" in utterance or "confusing" in utterance)
    return (clarification_slots or had_confusion_word) and state_manager.last_state_active_rg != 'WIKI'

def repetition_complaint(state_manager):
    state = state_manager.current_state
    utterance = state.text
    repetition_slots = ComplaintRepetitionTemplate().execute(utterance)
    return repetition_slots

def privacy_complaint(state_manager):
    state = state_manager.current_state
    utterance = state.text
    privacy_slots = ComplaintPrivacyTemplate().execute(utterance)
    return privacy_slots

def you_cant_do_that_complaint(state_manager):
    state = state_manager.current_state
    utterance = state.text
    return utterance.startswith("you can't")

def doesnt_make_sense_complaint(state_manager):
    state = state_manager.current_state
    utterance = state.text
    return 'doesn\'t make sense' in utterance

def generic_complaint(state_manager):
    state = state_manager.current_state
    return state.dialogact['probdist']['complaint'] > COMPLAINT_THRESHOLD

def user_asked_about_weather(state_manager):
    state = state_manager.current_state
    utterance = state.text
    weather_slots = WeatherTemplate().execute(utterance)
    return weather_slots

def user_asked_about_time(state_manager):
    state = state_manager.current_state
    utterance = state.text
    time_slots = WhatTimeIsItTemplate().execute(utterance)
    return time_slots
