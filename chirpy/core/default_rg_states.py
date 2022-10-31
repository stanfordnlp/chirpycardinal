from chirpy.core.response_generator.state import BaseState
from chirpy.response_generators.acknowledgment.state import State as AcknowledgmentState
from chirpy.response_generators.aliens.state import State as AliensState
from chirpy.response_generators.categories.state import State as CategoriesState
from chirpy.response_generators.closing_confirmation.state import State as ClosingConfirmationState
from chirpy.response_generators.fallback.state import State as FallbackState
from chirpy.response_generators.food.state import State as FoodState
from chirpy.response_generators.launch.state import State as LaunchState
from chirpy.response_generators.neural_chat.state import State as NeuralChatState
from chirpy.response_generators.neural_fallback.state import State as NeuralFallbackState
from chirpy.response_generators.offensive_user.state import State as OffensiveUserState
from chirpy.response_generators.one_turn_hack.state import State as OneTurnHackState
#from chirpy.response_generators.opinion2.state_actions import State as OpinionState
from chirpy.response_generators.personal_issues.state import State as PersonalIssuesState
from chirpy.response_generators.sports.state import State as SportsState
from chirpy.response_generators.pets.state import State as PetsState
from chirpy.response_generators.transition.state import State as TransitionState
from chirpy.response_generators.music.state import State as MusicState
from chirpy.response_generators.wiki2.state import State as WikiState
from chirpy.response_generators.reopen.state import State as ReopenState

DEFAULT_RG_STATES = {
    'ACKNOWLEDGMENT': AcknowledgmentState(),
    'ALEXA_COMMANDS': BaseState(),
    'ALIENS': AliensState(),
    'CATEGORIES': CategoriesState(),
    'CLOSING_CONFIRMATION': ClosingConfirmationState(),
    'COMPLAINT': BaseState(),
    'FALLBACK': FallbackState(),
    'FOOD': FoodState(),
    'LAUNCH': LaunchState(),
    'MUSIC': MusicState(),
    'NEURAL_CHAT': NeuralChatState(),
    'NEURAL_FALLBACK': NeuralFallbackState(),
    'OFFENSIVE_USER': OffensiveUserState(),
    'ONE_TURN_HACK': OneTurnHackState(),
    #'OPINION': OpinionState(),
    'PERSONAL_ISSUES': PersonalIssuesState(),
    'RED_QUESTION': BaseState(),
    'TRANSITION': TransitionState(),
    'WIKI': WikiState(),
    'REOPEN': ReopenState(),
}


def is_default_state(rg_name, state):
    return DEFAULT_RG_STATES[rg_name] == state
