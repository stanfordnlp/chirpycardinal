from chirpy.core.response_generator.regex_templates import *
from chirpy.core.regex.templates import *
from enum import IntEnum, auto
from typing import Set, List
import logging

logger = logging.getLogger('chirpylogger')


class ResponseType(IntEnum):
    """
    Base Response Types
    """
    DISINTERESTED = auto()  # User displays negative navigational intent
    CHANGE_TOPIC = auto()  # User indicates intention to change topic
    REQUEST_REPEAT = auto()
    YES = auto()  # User responds with a statement that contains a yes-phrase
    NO = auto()  # User responds with a statement that contains a no-phrase
    QUESTION = auto()  # User asks a question
    COMPLAINT = auto()
    DONT_KNOW = auto()  # User says they don't know
    DIDNT_KNOW = auto()  # User says they didn't know, probably in response to a TIL
    THATS = auto()  # User says "That's interesting" or something similar
    NOTHING = auto()  # User says "nothing", "i
    BACKCHANNEL = auto() # that's cool, okay, yes, nice


def add_response_types(response_type_enum, additional_response_types: List[str]):
    """
    Returns an IntEnum named 'ResponseType' with additional response types
    :param response_type_enum:
    :param additional_response_types:
    :return:
    """
    response_types = [i.name for i in response_type_enum]
    response_types += additional_response_types
    return IntEnum('ResponseType',
                   [(response_type, auto()) for response_type in response_types]
                   )


def identify_base_response_types(rg, utterance) -> Set[ResponseType]:
    retval = set()
    if is_disinterested(rg, utterance):
        retval.add(ResponseType.DISINTERESTED)

    if is_change_topic(rg, utterance):
        retval.add(ResponseType.CHANGE_TOPIC)

    if is_request_repeat(rg, utterance):
        retval.add(ResponseType.REQUEST_REPEAT)

    if is_no(rg, utterance):
        retval.add(ResponseType.NO)

    if is_yes(rg, utterance):
        retval.add(ResponseType.YES)

    if is_question(rg, utterance):
        retval.add(ResponseType.QUESTION)

    if is_complaint(rg, utterance):
        retval.add(ResponseType.COMPLAINT)

    if is_dont_know_response(rg, utterance):
        retval.add(ResponseType.DONT_KNOW)

    if is_didnt_know_response(rg, utterance):
        retval.add(ResponseType.DIDNT_KNOW)

    if is_thats_response(rg, utterance):
        retval.add(ResponseType.THATS)

    if is_nothing_response(rg, utterance):
        retval.add(ResponseType.NOTHING)

    if is_backchannel(rg, utterance):
        retval.add(ResponseType.BACKCHANNEL)

    return retval


def is_disinterested(rg, utterance):
    """
    Classifies whether the user sounds disinterested
    """
    return rg.state_manager.current_state.navigational_intent.neg_intent or \
           DisinterestedTemplate().execute(utterance) is not None


def is_no(rg, utterance):
    return NoTemplate().execute(utterance) is not None or rg.state_manager.current_state.dialogact['is_no_answer']


def is_question(rg, utterance):
    return rg.state_manager.current_state.question['is_question']


def is_yes(rg, utterance):
    return (YesTemplate().execute(utterance) is not None and NotYesTemplate().execute(utterance) is None) \
           or rg.state_manager.current_state.dialogact['is_yes_answer']


def is_complaint(rg, utterance):
    return rg.state_manager.current_state.dialogact['top_1'] == 'complaint'


def is_change_topic(rg, utterance):
    return ChangeTopicTemplate().execute(utterance) is not None


def is_request_repeat(rg, utterance):
    return RequestRepeatTemplate().execute(utterance) is not None or SayThatAgainTemplate().execute(
        utterance) is not None


def is_dont_know_response(rg, utterance):
    template_match = DontKnowTemplate().execute(utterance) is not None
    is_difficult = any([x in utterance for x in ['tough', 'tricky', 'difficult']]) and rg.get_current_entity(
        initiated_this_turn=True) is None
    return template_match or is_difficult


def is_thats_response(rg, utterance):
    return ThatsTemplate().execute(utterance) is not None


def is_didnt_know_response(rg, utterance):
    return DidntKnowTemplate().execute(utterance) is not None or \
           (SurprisedReallyTemplate().execute(utterance) is not None and len(utterance) <= 15)


def is_nothing_response(rg, utterance):
    return NotThingTemplate().execute(utterance) is not None


def is_backchannel(rg, utterance):
    return BackChannelingTemplate().execute(utterance) is not None
