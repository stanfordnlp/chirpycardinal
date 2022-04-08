"""
    Trenton Chang, Caleb Chiam - Nov. 2020
    personal_issues_utils.py

    The following file contains utility functions used by the PersonalIssuesResponseGenerator.

"""

from chirpy.response_generators.personal_issues.regex_templates import *
from chirpy.core.response_generator.response_type import add_response_types, ResponseType
from chirpy.annotators.corenlp import Sentiment
import logging
logger = logging.getLogger('chirpylogger')

ADDITIONAL_RESPONSE_TYPES = ['PERSONAL_SHARING_NEGATIVE', 'IS_CONTINUED_SHARING', 'SHORT_RESPONSE',
                             'NONCOMMITTAL', 'GRATITUDE', 'UNKNOWN_TYPE']

ResponseType = add_response_types(ResponseType, ADDITIONAL_RESPONSE_TYPES)

# logger.primary_info("Personal issues ResponseType:", str(list(ResponseType)))

def is_gratitude_response(rg, utterance):
    """Classifies whether the user sounds grateful.

    Args:
        rg (ResponseGenerator): the current rg.
        utterance (str): what the user said.

    Returns:
        bool: a boolean variable representing whether the user is grateful.
    """
    return rg.state_manager.current_state.corenlp['sentiment'] >= Sentiment.NEUTRAL and \
           GratitudeTemplate().execute(utterance) is not None and NegatedGratitudeTemplate().execute(utterance) is None


def is_short_response(utterance):
    return len(utterance.split()) <= 2


def is_noncommittal_response(rg, utterance):
    """Classifies whether the user sounds noncommittal.

    Args:
        rg (ResponseGenerator): the current rg.
        utterance (str): what the user said.

    Returns:
        bool: a boolean variable representing whether the user is noncommittal.
    """
    # possible signals: back=channeling, sentence length, descriptive language (I-statements, adjectives?)
    top_da = rg.state_manager.current_state.dialogact['top_1']
    return top_da in ['back-channeling'] or len(utterance.split()) <= 5


PERSONAL_ISSUE_THRESHOLD = 0.7
def is_personal_issue(rg, utterance):
    sentiment = rg.state_manager.current_state.corenlp['sentiment']
    template_match = PersonalSharingTemplate().execute(utterance) is not None
    # logger.primary_info(f"Personal sharing template match: {template_match}")
    return sentiment <= Sentiment.NEUTRAL and template_match
    # return (sentiment <= Sentiment.NEUTRAL and
    #        rg.state_manager.current_state.dialogact['personal_issue_score'] >= PERSONAL_ISSUE_THRESHOLD and
    #        not rg.state_manager.current_state.question['is_question']) or template_match


NEUTRAL_SHARING_THRESHOLD = 0.45
def is_continued_sharing(rg, utterance):
    num_tokens = len(utterance.split())
    neg_emotion = NegativeEmotionRegexTemplate().execute(utterance) is not None
    long_response_with_personal_pronouns = num_tokens >= 5 and \
                                           PersonalPronounRegexTemplate().execute(utterance) is not None
    long_sharing = num_tokens >= 10
    personal_disclosure = rg.state_manager.current_state.dialogact['personal_issue_score'] >= NEUTRAL_SHARING_THRESHOLD
    change_topic = ChangeTopicTemplate().execute(utterance) is not None
    logger.primary_info(f"Continued sharing checks: neg_emotion {neg_emotion is not None}, "
                        f"is long response with personal pronouns {long_response_with_personal_pronouns}, "
                        f"personal_disclosure {personal_disclosure}")

    if rg.state_manager.current_state.question['is_question'] or change_topic:
        return False

    template_match = PersonalSharingContinuedTemplate().execute(utterance) is not None

    return neg_emotion or long_response_with_personal_pronouns or personal_disclosure or long_sharing or template_match


def backchannel_appropriate(rg, utterance):
    if rg.state_manager.current_state.question['is_question']:
        logger.primary_info("PI_RG: Is question so backchannel not appropriate")
        return False
    if is_noncommittal_response(rg, utterance):
        logger.primary_info("PI_RG: Is noncommittal so backchannel not appropritate")
        return False
    if len(utterance.split()) >= 10:
        return True
