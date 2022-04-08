import logging
from typing import List, Dict, Set, Optional  # NOQA

from chirpy.core.callables import Annotator, get_url
from chirpy.core.state_manager import StateManager
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.annotators.navigational_intent.regex_templates import NegativeNavigationTemplate, PositiveNavigationTemplate, SomethingElseTemplate, THIS, NavigationQuestionTemplate
from chirpy.core.util import replace_phrase, remove_punc, contains_phrase

logger = logging.getLogger('chirpylogger')

HESITATE = "<HESITATE>"
CURRENT_TOPIC = "<CURRENT_TOPIC>"

EXCEPTIONS = ['we need to talk about kevin']  # if this is in a user utterance, assume its navigational intent is none

class NavigationalIntentOutput(object):
    """
    This class represents the navigational intent (if any) of the user's utterance. It has four attributes:

    - pos_intent: bool. This is True iff the user is saying they DO want to talk about something

    - pos_topic: this has 4 cases:
        1. pos_topic = "<HESITATE>". This means the user said something like "let's talk about"
        2. pos_topic = "<CURRENT_TOPIC>". This means the user said something like "let's talk about it"
        3. pos_topic = (topic: str, about_keyword: bool). The topic is the text that came after the positive navigational
              phrase, and about_keyword = True iff the keyword "about" appeared before the topic.
              For example, "can we chat about architecture please" -> topic = "architecture please", about_keyword = True
              For example, "can we chat architecture please" -> topic = "architecture please", about_keyword = False
        4. pos_topic = None. If pos_intent=True, this means the user supplied no topic e.g. just said "i wanna talk"

    - neg_intent: bool. This is True iff the user is saying they DON'T want to talk about something

    - neg_topic: this has has 4 cases:
        1. neg_topic = "<HESITATE>". This means the user said something like "i don't want to talk about"
        2. pos_topic = "<CURRENT_TOPIC>". This means the user said something like "let's not talk about it"
        3. neg_topic = (topic: str, about_keyword: bool). The topic is the text that came after the negative navigational
              phrase, and about_keyword = True iff the keyword "about" appeared before the topic.
              For example, "stop talking about architecture please" -> topic = "architecture please", about_keyword = True
              For example, "stop talking architecture please" -> topic = "architecture please", about_keyword = False
        4. neg_topic = None. If neg_intent=True, this means the user supplied no topic e.g. just said "i don't wanna talk"
    """
    def __init__(self, pos_intent: bool = False, pos_topic=None, neg_intent: bool = False, neg_topic=None):
        self.pos_intent = pos_intent
        self.validate_topic(pos_topic)
        self.pos_topic = pos_topic
        self.neg_intent = neg_intent
        self.validate_topic(neg_topic)
        self.neg_topic = neg_topic

    def validate_topic(self, topic):
        """Checks topic is the right type"""
        if isinstance(topic, str):
            return
        elif topic is None:
            return
        else:
            assert isinstance(topic, tuple)
            assert len(topic) == 2
            (topic, about_keyword) = topic
            assert isinstance(topic, str)
            assert isinstance(about_keyword, bool)

    @property
    def pos_topic_is_hesitate(self) -> bool:
        """Returns True iff the user said something like 'i want to talk about'"""
        return self.pos_topic == HESITATE

    @property
    def neg_topic_is_hesitate(self) -> bool:
        """Returns True iff the user said something like 'i don't want to talk about'"""
        return self.neg_topic == HESITATE

    @property
    def pos_topic_is_current_topic(self) -> bool:
        """Returns True iff the user said something like 'i want to talk about this'"""
        return self.pos_topic == CURRENT_TOPIC

    @property
    def neg_topic_is_current_topic(self) -> bool:
        """Returns True iff the user said something like 'i don't want to talk about this'"""
        return self.neg_topic == CURRENT_TOPIC

    @property
    def pos_topic_is_supplied(self) -> bool:
        """
        Returns True iff the user said something like 'i want to talk (about) X' where X is some nonempty string
        that doesn't mean "current topic" or "something else".
        """
        return isinstance(self.pos_topic, tuple)

    @property
    def neg_topic_is_supplied(self) -> bool:
        """
        Returns True iff the user said something like 'i don't want to talk (about) X' where X is some nonempty string
        that doesn't mean "current topic" or "something else".
        """
        return isinstance(self.neg_topic, tuple)

    def __repr__(self):
        return f"<NavigationalIntentOutput: pos_intent={self.pos_intent}, pos_topic={self.pos_topic}, " \
               f"neg_intent={self.neg_intent}, neg_topic={self.neg_topic}>"


def is_something_else(topic: Optional[str], somethingelse_template: RegexTemplate) -> bool:
    """Returns True iff topic matches SomethingElseRegexTemplate"""
    if not topic:
        return False
    slots = somethingelse_template.execute(topic)
    logger.info(f'Ran SomethingElseTemplate on "{topic}" and got: {slots}')
    return slots is not None


def is_this(topic: Optional[str]) -> bool:
    """Returns True iff topic consists entirely of THIS words"""
    if not topic:
        return False
    return all(word in THIS for word in topic.split())


def get_phrase_from_slots(slots: dict) -> Optional[str]:
    """
    Given slots (the output of PositiveNavigation or NegativeNavigation RegexTemplate), return the full phrase that
    matched. For example if slots={'nav_about': 'i don't want to talk about', 'slots': 'movies'} then the output is
    "i don't want to talk about movies".
    """
    if 'change_the_subject' in slots:
        return slots['change_the_subject']
    elif 'nav_about' in slots:
        if 'topic' in slots:
            return "{} {}".format(slots['nav_about'], slots['topic'])
        else:
            return slots['nav_about']
    elif 'nav' in slots:
        if 'topic' in slots:
            return "{} {}".format(slots['nav'], slots['topic'])
        else:
            return slots['nav']
    else:
        return None


def get_intent_and_topic(slots: dict):
    """
    Given slots, which is the output of the PositiveNavigation or NegativeNavigation RegexTemplate, return the
    intent (bool) and topic (str/None/tuple) - see NavigationalIntentOutput.
    """
    if 'topic' in slots and is_this(slots['topic']):  # if the user is saying "let's (not) talk about this"
        return True, CURRENT_TOPIC  # this means the user does/doesn't want to talk about the current topic
    elif slots:
        if 'topic' in slots and slots['topic']:  # if there's a topic
            about_keyword = 'nav_about' in slots  # about_keyword=True iff the user said "about"
            return True, (slots['topic'], about_keyword)  # the user wants to talk about this topic
        else:  # no topic
            if 'nav_about' in slots:  # if there's no topic but the user said the "about" keyword
                return True, HESITATE  # that means they hesitated
            else:  # if there's no topic but the user didn't say the "about" keyword
                return True, None  # that means they're giving a navigational intent without a topic
    else:
        return False, None  # no navigational intent


def get_nav_intent(user_utterance: str, history: List[str]) -> NavigationalIntentOutput:
    """
    Runs PositiveNavigational and NegativeNavigational RegexTemplates on user_utterance and returns a
    NavigationalIntentOutput. We can detect utterances that contain positive intent, negative intent, both or neither.
    """
    for exception_text in EXCEPTIONS:
        if contains_phrase(user_utterance, {exception_text}):
            logger.primary_info(f"user utterance '{user_utterance}' contains exception text '{exception_text}', so marking navigational intent as none")
            return NavigationalIntentOutput()
    # if is_question:
    #     logger.primary_info(f"user_utterance '{user_utterance}' is marked as is_question, so assuming navigational_intent is none")
    #     return NavigationalIntentOutput()

    pos_template = PositiveNavigationTemplate()
    neg_template = NegativeNavigationTemplate()
    somethingelse_template = SomethingElseTemplate()
    nav_question_template = NavigationQuestionTemplate()

    # Check whether the last bot utterance was asking a general "what do you want to talk about?" question
    if history:
        bot_last_utt = history[-1].lower()  # lowercase
        bot_last_utt = remove_punc(bot_last_utt, keep=["'"])  # remove punctuation except apostrophe
        bot_asked_nav_question = nav_question_template.execute(bot_last_utt) is not None  # bool
        logger.info(f'Ran NavQuestionTemplate on last bot utterance "{bot_last_utt}". bot_asked_nav_question={bot_asked_nav_question}.')
    else:
        bot_asked_nav_question = False

    # Run NegNav template
    neg_slots = neg_template.execute(user_utterance)
    neg_slots = {} if not neg_slots else neg_slots  # dict
    logger.info(f'Ran NegNavTemplate on "{user_utterance}" and got: {neg_slots}')

    # Get the texts we want to run PosNav template on
    texts_for_postemplate = set()

    # We want to run PosNav on parts of the user utterance that aren't in neg_phrase
    neg_phrase = get_phrase_from_slots(neg_slots)  # str or None
    user_utterance_minus_negphrase = replace_phrase(user_utterance, neg_phrase, '')
    texts_for_postemplate.add(user_utterance_minus_negphrase)

    # We also want to run PosNav on the topic in neg_slots.
    # For example if the user said "i don't want to talk about this let's talk about cats", then
    # neg_topic = "this let's talk about cats". So we want to check for PosNav in neg_topic.
    if 'topic' in neg_slots:
        texts_for_postemplate.add(neg_slots['topic'])

    # Run PosNav template
    posnav_results = [pos_template.execute(t) for t in texts_for_postemplate]  # list of dicts
    logger.info(f'Ran PosNavTemplate on: {texts_for_postemplate} and got: {posnav_results}')

    # Remove posnav results that didn't match
    posnav_results = [slots for slots in posnav_results if slots]

    # Sort posnav_results, preferring those with a topic and the "about" keyword, and take the first one
    posnav_results = sorted(posnav_results, key=lambda slots: ('topic' in slots, 'nav_about' in slots))
    if posnav_results:
        logger.info(f'posnav_results after sorting: {posnav_results}. Choosing first one.')
        pos_slots = posnav_results[0]  # dict
    else:
        pos_slots = {}

    # If there is a PosNav match, remove pos_phrase from neg_slots.
    # For example if the user said "i don't want to talk about this let's talk about cats", then
    # we want to remove pos_phrase = "let's talk about cats" from neg_topic = "this let's talk about cats".
    if 'topic' in neg_slots:
        neg_slots['topic'] = replace_phrase(neg_slots['topic'], get_phrase_from_slots(pos_slots), '')

    # If the user isn't giving an explicit pos/neg nav intent, and the bot asked "what do you want to talk about" on
    # the previous turn, regard the user's whole utterance as the topic, without the "about" keyword.
    if not pos_slots and not neg_slots and bot_asked_nav_question:
        logger.primary_info(f'Bot asked NavigationalQuestion on the previous turn, so regarding '
                            f'user_utterance="{user_utterance}" as a PosNav topic')
        pos_slots = {'topic': user_utterance}

    # Get pos_intent and pos_topic
    if 'topic' in neg_slots and is_something_else(neg_slots['topic'], somethingelse_template):  # if the user is saying "i don't want to talk about something else" (rare)
        pos_intent, pos_topic = True, CURRENT_TOPIC  # this means the user wants to talk about the current topic
        neg_slots = {}  # reset neg_slots so we don't "double report" the intent
    else:
        pos_intent, pos_topic = get_intent_and_topic(pos_slots)

    # Get neg_intent and neg_topic
    if 'topic' in pos_slots and is_something_else(pos_slots['topic'], somethingelse_template):  # if the user is saying "i want to talk about something else"
        neg_intent, neg_topic = True, CURRENT_TOPIC  # this means the user doesn't want to talk about the current topic
        pos_intent, pos_topic = False, None  # reset pos intent so we don't "double report" the intent
    elif 'change_the_subject' in neg_slots:  # if the user is saying "change the subject"
        neg_intent, neg_topic = True, CURRENT_TOPIC  # this means the user doesn't want to talk about the current topic
    else:
        neg_intent, neg_topic = get_intent_and_topic(neg_slots)

    output = NavigationalIntentOutput(pos_intent, pos_topic, neg_intent, neg_topic)

    logger.primary_info('Navigational intent for user_utterance="{}": {}'.format(user_utterance, output))
    return output


class NavigationalIntentModule(Annotator):
    name='navigational_intent'
    """
    Runs PositiveNavigational and NegativeNavigational RegexTemplates on user_utterance and returns a NavigationalIntentOutput.
    """
    def __init__(self, state_manager: StateManager, timeout=1.5, url=None, input_annotations=[]):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url or 'local', input_annotations=input_annotations)

    def get_default_response(self):
        return NavigationalIntentOutput()

    def execute(self, user_utterance: Optional[str] = None, history: List[str] = []) -> NavigationalIntentOutput:
        """
        Determines navigational intent of user_utterance with history context.
        If user_utterance is not provided, uses utterance in current state.
        """
        if user_utterance is None:
            user_utterance = self.state_manager.current_state.text
            history = self.state_manager.current_state.history
        if not user_utterance:
            return self.get_default_response()
        return get_nav_intent(user_utterance, history)


if __name__ == '__main__':
    # You can use this code to test the nav intent module
    from functools import lru_cache
    from chirpy.annotators.question import QUESTION_THRESHOLD

    # Setup logging
    from chirpy.core.logging_utils import setup_logger, LoggerSettings

    LOGTOSCREEN_LEVEL = logging.INFO
    logger_settings = LoggerSettings(logtoscreen_level=LOGTOSCREEN_LEVEL, logtoscreen_usecolor=True,
                                     logtofile_level=None, logtofile_path=None,
                                     logtoscreen_allow_multiline=True, integ_test=False, remove_root_handlers=False)
    setup_logger(logger_settings)

    # Init question module
    import requests
    import json
    class TestModule:
        def __init__(self, url):
            self.url = url
        def execute(self, data):
            response = requests.post(self.url, data=json.dumps(data), headers={'content-type': 'application/json'}, timeout=10)
            return response
    url = get_url("question")
    question_module = TestModule(url)

    @lru_cache(maxsize=1024)
    def get_question_annotation(user_utterance):
        question_output = question_module.execute({'utterance': user_utterance}).json()
        question_prob = question_output['response'][0]
        return (question_prob >= QUESTION_THRESHOLD)


    bot_utterance = ""
    user_utterance = "i'd rather not talk about this"
    # is_question = get_question_annotation(user_utterance)
    get_nav_intent(user_utterance, [bot_utterance])
