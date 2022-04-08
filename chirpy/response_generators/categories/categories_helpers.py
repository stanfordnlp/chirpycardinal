import logging
from typing import Optional, Tuple
from chirpy.core.util import contains_phrase
from chirpy.response_generators.categories.regex_templates import CategoriesTemplate
from chirpy.response_generators.categories.categories import CATEGORYNAME2CLASS, ACTIVATIONPHRASE2CATEGORYNAME

logger = logging.getLogger('chirpylogger')

QUESTION_CONNECTORS = [
    "So ",
    "This is a little random but ",
    "There's actually something else I wanted to ask you about, ",
    "This is unrelated but I was just thinking, ",
    "So, I just thought of something. ",
    "Anyway, um, on another subject. ",
    "Hmm, so, on another topic. ",
    "Oh hey, I just remembered another thing I've been wondering about. ",
    "Anyway, there’s actually an unrelated thing I wanted to know. ",
    "This is a bit random, but I just remembered something I wanted to ask you. "
]

def get_user_initiated_category(user_utterance, current_state) -> Tuple[Optional[str], bool]:
    """
    If the user utterance matches RegexTemplate, return the name of the category they're asking for.
    Otherwise return None.

    Returns:
        category: the category being activated
        posnav: whether the user has posnav
    """
    slots = CategoriesTemplate().execute(user_utterance)

    # Legacy code; not removing in case it breaks something
    # if slots is not None and slots["keyword"] in ACTIVATIONPHRASE2CATEGORYNAME:
    #     category_name = ACTIVATIONPHRASE2CATEGORYNAME[slots['keyword']]
    #     logger.primary_info(f'Detected categories intent for category_name={category_name} and slots={slots}.')
    #     return category_name, True

    # If any activation phrase is in the posnav slot, activate with force_start
    nav_intent = getattr(current_state, 'navigational_intent', None)
    if nav_intent and nav_intent.pos_intent and nav_intent.pos_topic_is_supplied:
        pos_topic = nav_intent.pos_topic[0]  # str
        for activation_phrase, category_name in ACTIVATIONPHRASE2CATEGORYNAME.items():
            if contains_phrase(pos_topic, {activation_phrase}, lowercase_text=False, lowercase_phrases=False, remove_punc_text=False, remove_punc_phrases=False):
                logger.primary_info(f"Detected categories activation phrase '{activation_phrase}' in posnav slot, so categories is activating with force_start")
                return category_name, True

    # If any activation phrase is in the user utterance, activate with can_start
    for activation_phrase, category_name in ACTIVATIONPHRASE2CATEGORYNAME.items():
        if contains_phrase(user_utterance, {activation_phrase}, lowercase_text=False, lowercase_phrases=False, remove_punc_text=False, remove_punc_phrases=False):
            logger.primary_info(f"Detected categories activation phrase '{activation_phrase}' in utterance (but not in a posnav slot), so categories is activating with can_start")
            return category_name, False

    return None, False