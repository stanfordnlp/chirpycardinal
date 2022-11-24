from enum import Enum


# higher number is higher priority
# the numbers themselves aren't important, only the relative ordering
class ResponsePriority(int, Enum):

    # Use this when the user is NOT already in the RG, but the RG should force to take control
    # e.g. red question responder, or the user is explicitly requesting the RG
    FORCE_START = 5

    # Use this when the user is already in the RG, and the RG has a good next response (only overridden by FORCE_START)
    STRONG_CONTINUE = 4

    # Use this when the user is NOT already in the RG, but the RG has a possible response
    # (but the response isn't good enough to override a STRONG_CONTINUE)
    CAN_START = 3

    # Use this when the user is already in the RG, and the RG has a not-so-good next response
    # (i.e. the response should be overridden by any CAN_STARTs)
    WEAK_CONTINUE = 2

    # Only the Fallback RG uses this priority.
    # We call the Fallback RG's utterances "universal fallbacks" to distinguish from RG-specific fallback utterances
    UNIVERSAL_FALLBACK = 1

    # Use this when the RG has no response (i.e. text is None)
    NO = 0

    def __str__(self):
        return self._name_


class PromptType(int, Enum):
    # This category should ONLY be used when forcing a smooth transition from one RG to the other. In other words,
    # it only makes sense for an RG to pass off control to one of a small subset of prompts, which are denoted with
    # FORCE_START
    FORCE_START = 4

    # A current topic prompt is one that makes use of the cur_entity
    CURRENT_TOPIC = 3

    # A contextual prompt is one that doesn't make use of the cur_entity, but is in some way conditioned on the
    # conversation so far
    CONTEXTUAL = 2

    # A generic prompt is one that isn't conditioned on the conversation so far
    GENERIC = 1

    # Use this when the RG has no prompt (i.e. text is None)
    NO = 0


# Higher number is higher priority. The numbers themselves aren't important, only the relative ordering.
# TiebreakPriority is only used for tiebreaks AFTER sorting by ResponsePriority
# This is only used for responses, not prompts
class TiebreakPriority(Enum):
    CLOSING_CONFIRMATION = 250
    OFFENSIVE_USER = 200
    COMPLAINT = 175
    SYMBOLIC_RESPONSE = 160
    RED_QUESTION = 150
    LAUNCH = 100
    TRANSITION = 71
    PERSONAL_ISSUES = 69
    FOOD = 68
    NEURAL_CHAT = 66
    ALIENS = 66
    OPINION = 63
    ACKNOWLEDGMENT = 62
    EVI = 58
    NEWS = 65
    WIKI = 64
    CATEGORIES = 60
    MUSIC = 66
    NEURAL_FALLBACK = 5  # fallback should always be lowest priority i.e. last resort
    FALLBACK = 0  # fallback should always be lowest priority i.e. last resort

# Defines a probability distribution over the types of prompts
PROMPT_TYPE_DIST = {
    PromptType.FORCE_START: 10**12,
    PromptType.CURRENT_TOPIC: 10**6,
    PromptType.CONTEXTUAL: 7,
    PromptType.GENERIC: 3,
    PromptType.NO: 0.0
}

# Defines a probability distribution over response generators that signifies the likelihood of that response
# generator's prompt being given when the prompt type chosen is force_start.
# Typically there is only one or zero FORCE_START prompts per turn, so the relative probabilities here don't usually matter.
FORCE_START_PROMPT_DIST = {
    "OPINION": 1,
    "WIKI": 1,
    "OFFENSIVE_USER": 1,
    "RED_QUESTION": 1,
    "LAUNCH": 1,
    "CATEGORIES": 1,
    "NEURAL_FALLBACK": 1,
    "FALLBACK": 1,
    "CLOSING_CONFIRMATION": 1,
    "FOOD": 1,
    'ALIENS': 1,
    "TRANSITION": 1,
    "REOPEN": 1,
    "NEURAL_CHAT": 0.000001,
    "MUSIC": 1
}

# Defines a probability distribution over response generators that signifies the likelihood of that response
# generator's prompt being given when the prompt type chosen is contextual. Response generators with a 0.0
# probability of being picked never give contextual prompts.
CURRENT_TOPIC_PROMPT_DIST = {
    "MUSIC": 1,
    "OPINION": 1,
    "WIKI": 1,
    'NEURAL_CHAT': 1,
    "OFFENSIVE_USER": 0.0,
    "RED_QUESTION": 0.0,
    "LAUNCH": 0.0,
    "ONE_TURN_HACK": 0.0,
    "CATEGORIES": 1,
    "NEURAL_FALLBACK": 0.0,
    "FALLBACK": 0.0,
    "CLOSING_CONFIRMATION": 0.0,
    'ALIENS': 0.0,
    "TRANSITION": 1,
    "REOPEN": 0,
}


# Defines a probability distribution over response generators that signifies the likelihood of that response
# generator's prompt being given when the prompt type chosen is contextual. Response generators with a 0.0
# probability of being picked never give contextual prompts.
CONTEXTUAL_PROMPT_DIST = {
    "MUSIC": 0.3,
    "FOOD": 0.3,
    "OPINION": 0.1,
    "WIKI": 0.25,
    'NEURAL_CHAT': 0.3,
    "OFFENSIVE_USER": 0.0,
    "RED_QUESTION": 0.0,
    "LAUNCH": 0.0,
    "ONE_TURN_HACK": 0.0,
    "CATEGORIES": 0.3,
    "NEURAL_FALLBACK": 0.0,
    "FALLBACK": 0.0,
    "CLOSING_CONFIRMATION": 0.0,
    "CORONAVIRUS": 0.0,
    'ALIENS': 0.0,
    'TRANSITION': 0.5,
    'REOPEN': 0.0
}

# Defines a probability distribution over response generators that signifies the likelihood of that response
# generator's prompt being given when the prompt type chosen is generic. Response generators with a 0.0
# probability of being picked never give generic prompts.
GENERIC_PROMPT_DIST = {
    "CATEGORIES": 3,
    "MUSIC": 1.5,
    "OPINION": 1,
    "WIKI": 1,
    "FALLBACK": 0.0001,
    "FOOD": 1.5,
    'NEURAL_CHAT': 2,
    'ALIENS': 2,
    "OFFENSIVE_USER": 0,
    "RED_QUESTION": 0,
    "LAUNCH": 0,
    "REOPEN": 2,
}

PROMPT_DISTS_OVER_RGS = {
    PromptType.FORCE_START: FORCE_START_PROMPT_DIST,
    PromptType.CURRENT_TOPIC: CURRENT_TOPIC_PROMPT_DIST,
    PromptType.CONTEXTUAL: CONTEXTUAL_PROMPT_DIST,
    PromptType.GENERIC: GENERIC_PROMPT_DIST
}
