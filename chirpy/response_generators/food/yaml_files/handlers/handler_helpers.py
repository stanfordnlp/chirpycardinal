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


import os
STOPWORDS_FILEPATH = 'chirpy/data/long_stopwords.txt'
STOPWORDS = load_text_file(STOPWORDS_FILEPATH)

OMPLAINT_THRESHOLD = 0.91
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

def user_wants_name_correction(state_manager):
    state = state_manager.current_state
    utterance = state.text
    my_name_slots = MyNameIsNonContextualTemplate().execute(utterance)
    not_my_name_slots = MyNameIsNotTemplate().execute(utterance)
    if my_name_slots and state_manager.last_state_active_rg and state_manager.last_state_active_rg != 'LAUNCH':
        return my_name_slots
    if not_my_name_slots:
        return not_my_name_slots

def user_requested_name(state_manager):
    state = state_manager.current_state
    utterance = state.text
    request_name_slots = RequestNameTemplate().execute(utterance)
    return request_name_slots

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

def user_interrupted(state_manager) -> bool:
    state = state_manager.current_state
    user_utterance = state.text
    interruption_slots = InterruptionQuestionTemplate().execute(user_utterance)
    return interruption_slots

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

def handle_weather(self, slots):
    last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
    return ResponseGeneratorResult(
            text=f"I live in the cloud so I'm not sure what the weather is like on earth! But anyway, I was just saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

def handle_what_time(self, slots):
    last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
    return ResponseGeneratorResult(
            text=f"I live in the cloud so I'm not sure what time it is on earth! But anyway, I was just saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

def handle_repetition_request(self, slots):
    if any(self.get_previous_bot_utterance().startswith(phrase) for phrase in CONFIRM_SAYING_PHRASES + CORRECT_SAYING_PHRASES + REPETITION_APOLOGY + response_lists.CLARIFICATION_COMPLAINT_RESPONSE):
        # If asked to repeat twice in a row, change topic instead
        return ResponseGeneratorResult(text=f"{self.choose(SORRY_FOR_CONNECTION)}", #..."anyway, I was thinking.... [prompt continues]"
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self.ConditionalState())

    return ResponseGeneratorResult(text=f"{self.choose(REPETITION_APOLOGY)} What I said was, {self.get_previous_bot_utterance()}",
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self._construct_no_update_conditional_state())

def handle_user_name_correction(self, slots):
    apology = "Oops, it sounds like I got your name wrong. I'm so sorry about that! I won't make that mistake again."
    last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
    setattr(self.state_manager.user_attributes, 'name', None)
    setattr(self.state_manager.user_attributes, 'discussed_aliens', False)
    return ResponseGeneratorResult(
            text=f"{apology} Anyway, as I was saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

def handle_name_request(self, slots):
    last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
    user_name = getattr(self.state_manager.user_attributes, 'name', None)
    if user_name:
        response = f"If I remember correctly, your name is {user_name}."
    else:
        response = "Hmm, I don't think you gave me your name."
    return ResponseGeneratorResult(text=f"{response} Anyway, as I was saying: {last_sentence}",
                            priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                            state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                            conditional_state=self._construct_no_update_conditional_state())

def handle_cutoff_user(self, slots):
    if any(self.get_previous_bot_utterance().startswith(phrase) for phrase in USER_REPEAT_PHRASES):
        # If asked to repeat twice in a row, change topic instead
        return ResponseGeneratorResult(text=f"{self.choose(SORRY_FOR_CONNECTION)}", #..."anyway, I was thinking.... [prompt continues]"
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self.ConditionalState())
    return ResponseGeneratorResult(
            text=self.choose(response_lists.CUTOFF_USER_RESPONSE),
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )

def handle_age_request(self, slots):
    last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
    return ResponseGeneratorResult(
            text=f"{self.choose(response_lists.HANDLE_AGE_RESPONSE)} But anyway, I was just saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

def first_to_second_person(response) -> str:
    result = ' '.join([FP_TO_SP.get(word, word) for word in response.split()])
    return result



def handle_abilities_question(self, slots):
    return ResponseGeneratorResult(text=f"{self.choose(response_lists.HANDLE_ABILITIES_RESPONSE)}",
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self._construct_no_update_conditional_state())

def handle_personal_question(self, slots):
    continuation = slots.get('action', '')
    if continuation:
        best_response = self.get_neural_response()
        return ResponseGeneratorResult(text=f"{self.choose(THANK_INQUIRY_PHRASES)} {best_response}",
                                        priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                        state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                        conditional_state=self._construct_no_update_conditional_state())

def handle_user_clarification(self, slots):
    # check 1-gram overlap -- proxy to see if user is repeating what bot says
    bot_words = self.get_previous_bot_utterance().split()
    non_trivial_overlap_tokens = set(self.utterance.split()) & set(bot_words) - set(STOPWORDS)
    logger.debug(f"Got non-trivial overlap {non_trivial_overlap_tokens} from '{self.utterance.split()}', '{self.get_previous_bot_utterance()}'")

    if any(self.get_previous_bot_utterance().startswith(phrase) for phrase in CONFIRM_SAYING_PHRASES + CORRECT_SAYING_PHRASES + REPETITION_APOLOGY + response_lists.CLARIFICATION_COMPLAINT_RESPONSE):
        # If asked to repeat twice in a row, change topic instead
        return ResponseGeneratorResult(text=f"{self.choose(SORRY_FOR_CONNECTION)}", #..."anyway, I was thinking.... [prompt continues]"
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self.ConditionalState())

    if len(non_trivial_overlap_tokens):
        second_personified_user_query = first_to_second_person(slots.get('query', ''))
        repeated = " ".join([word for word in second_personified_user_query.split() if word in bot_words])
        return ResponseGeneratorResult(text=f"{self.choose(CONFIRM_SAYING_PHRASES)}: {repeated}.", priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self._construct_no_update_conditional_state())
    else:
        last_sentence = get_last_sentence(self.get_previous_bot_utterance())
        return ResponseGeneratorResult(text=f"{self.choose(CORRECT_SAYING_PHRASES)}: {last_sentence}", priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self._construct_no_update_conditional_state())

def user_gave_nevermind(state_manager):
    state = state_manager.current_state
    utterance = state.text
    slots = NeverMindTemplate().execute(utterance)
    return slots

def handle_interruption_question(self, slots):
    if self.get_cache(f'{self.name}_last_bot_sentence') is not None: # in the tree. need to decide if user wants to navigate away or if asked a question that requires a neural response.
        back_transition = f"Anyway, as I was saying: {self.get_cache('last_bot_sentence')}"
        self.set_cache(f'{self.name}_last_bot_sentence', None)
        if user_gave_nevermind(self.state_manager.current_state):
            return ResponseGeneratorResult(
                    text=f"Oh, that's okay. {back_transition}",
                    priority=ResponsePriority.STRONG_CONTINUE,
                    needs_prompt=False,
                    state=self.state if self.state is not None else self.State(),
                    cur_entity=self.get_current_entity(),
                    conditional_state=self._construct_no_update_conditional_state()
                    )
        else:
            best_response = self.get_neural_response()
            return ResponseGeneratorResult(
                    text=f"{best_response} {back_transition}",
                    priority=ResponsePriority.STRONG_CONTINUE,
                    needs_prompt=False,
                    state=self.state if self.state is not None else self.State(),
                    cur_entity=self.get_current_entity(),
                    conditional_state=self._construct_no_update_conditional_state()
                    )
    else:
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        self.set_cache(f'{self.name}_last_bot_sentence', last_sentence)
        return ResponseGeneratorResult(
                text="Sure, what's up?",
                priority=ResponsePriority.STRONG_CONTINUE,
                needs_prompt=False,
                state=self.state if self.state is not None else self.State(),
                cur_entity=self.get_current_entity(),
                conditional_state=self._construct_no_update_conditional_state()
                )

def handle_chatty_phrase(self, slots):
    last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
    logger.primary_info(f"Chatty Phrase: {slots['chatty_phrase']}")
    return ResponseGeneratorResult(
            text=response_lists.ONE_TURN_RESPONSES.get(slots['chatty_phrase'], "Ok, I'd love to talk to you! What would you like to talk about?"),
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

def handle_story_request(self, slots):
    last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
    return ResponseGeneratorResult(
            text=f"Sure, here's a story someone told me. {self.choose(response_lists.STORIES)}. But anyway, as I was saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

def handle_personal_issue(self, slots):
    # overridden by NEURAL CHAT only
    return None

def handle_anything(self, slots):
    """slots is just boolean for this handlers"""
    return ResponseGeneratorResult(
            text=self.choose(['Okay!', 'Alright!', 'Hmm let me think.']),
            priority=ResponsePriority.CAN_START,
            needs_prompt=True,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )


