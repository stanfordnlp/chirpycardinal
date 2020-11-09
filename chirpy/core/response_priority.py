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
    RED_QUESTION = 150
    LAUNCH = 100
    CORONAVIRUS = 80
    ONE_TURN_HACK = 70
    NEURAL_CHAT = 68
    ACKNOWLEDGMENT = 67
    CATEGORIES = 60
    MUSIC = 38
    OPINION = 35
    WIKI = 30
    SHOWERTHOUGHTS = 10
    ALEXA_COMMANDS = 9
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
    "ONE_TURN_HACK": 1,
    "CATEGORIES": 1,
    "SHOWERTHOUGHTS": 1,
    "ALEXA_COMMANDS": 1,
    "NEURAL_FALLBACK": 1,
    "FALLBACK": 1,
    "CLOSING_CONFIRMATION": 1,
    "CORONAVIRUS": 1,

    # We're running an experiment with EmotionsTreelet and want to collect more data. So EmotionsTreelet is giving a
    # FORCE_START prompt to make sure we get more conversations. I don't want this to override another RG's legitimate
    # FORCE_START though, so I'm making the neural chat prob much smaller here.
    # That way, if NEURAL_CHAT is the only FORCE_START prompter, its prompt is chosen, but if there are any other
    # FORCE_START prompts, NEURAL_CHAT won't get chosen.
    "NEURAL_CHAT": 0.000001,
    "MUSIC": 1
}

# Defines a probability distribution over response generators that signifies the likelihood of that response
# generator's prompt being given when the prompt type chosen is contextual. Response generators with a 0.0
# probability of being picked never give contextual prompts.
CURRENT_TOPIC_PROMPT_DIST = {
    "OPINION": 1,
    "WIKI": 1,
    'NEURAL_CHAT': 1,
    "MUSIC": 1,
    "OFFENSIVE_USER": 0.0,
    "RED_QUESTION": 0.0,
    "LAUNCH": 0.0,
    "ONE_TURN_HACK": 0.0,
    "CATEGORIES": 1,
    "SHOWERTHOUGHTS": 0.0,
    "ALEXA_COMMANDS": 0.0,
    "NEURAL_FALLBACK": 0.0,
    "FALLBACK": 0.0,
    "CLOSING_CONFIRMATION": 0.0,
    "CORONAVIRUS": 0.0
}


# Defines a probability distribution over response generators that signifies the likelihood of that response
# generator's prompt being given when the prompt type chosen is contextual. Response generators with a 0.0
# probability of being picked never give contextual prompts.
CONTEXTUAL_PROMPT_DIST = {
    "OPINION": 0.1,
    "WIKI": 0.25,
    'NEURAL_CHAT': 0.3,
    "MUSIC": 0.3,
    "OFFENSIVE_USER": 0.0,
    "RED_QUESTION": 0.0,
    "LAUNCH": 0.0,
    "ONE_TURN_HACK": 0.0,
    "CATEGORIES": 0.3,
    "SHOWERTHOUGHTS": 0.0,
    "ALEXA_COMMANDS": 0.0,
    "NEURAL_FALLBACK": 0.0,
    "FALLBACK": 0.0,
    "CLOSING_CONFIRMATION": 0.0,
    "CORONAVIRUS": 0.0
}

# Defines a probability distribution over response generators that signifies the likelihood of that response
# generator's prompt being given when the prompt type chosen is generic. Response generators with a 0.0
# probability of being picked never give generic prompts.
GENERIC_PROMPT_DIST = {
    "CATEGORIES": 3,
    "OPINION": 1,
    "FALLBACK": 1,
    'NEURAL_CHAT': 3,
    "MUSIC": 1.5,
    "OFFENSIVE_USER": 0,
    "RED_QUESTION": 0,
    "LAUNCH": 0,
    "ONE_TURN_HACK": 0,
    "WIKI": 0,
    "SHOWERTHOUGHTS": 0,
    "ALEXA_COMMANDS": 0,
    "CORONAVIRUS": 0
}

PROMPT_DISTS_OVER_RGS = {
    PromptType.FORCE_START: FORCE_START_PROMPT_DIST,
    PromptType.CURRENT_TOPIC: CURRENT_TOPIC_PROMPT_DIST,
    PromptType.CONTEXTUAL: CONTEXTUAL_PROMPT_DIST,
    PromptType.GENERIC: GENERIC_PROMPT_DIST
}