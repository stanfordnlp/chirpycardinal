from enum import Enum, auto

class SmoothHandoff(Enum):
    """
    A smooth handoff is when one RG gives a response with needs_prompt=True, and another RG gives a prompt with
    PromptType=FORCE_START. This is used when we want a particular scripted transition.

    To make it easier to construct smooth handoffs without needing to write lots of extra code, you can
        (1) Create a unique identifier in this enumeration for your smooth handoff.
        (2) In its ResponseGeneratorResult, have the responding RG set smooth_handoff to the appropriate identifier in
            this enumeration. If the response is chosen, current_state.smooth_handoff will be set to the identifier.
        (3) In the prompting RG's get_prompt function, check whether current_state.smooth_handoff equals your
            identifier. If so, give the scripted prompt with PromptType=FORCE_START.
    """
    LAUNCH_TO_NEURALCHAT = auto()  # This signal is given at the end of the LAUNCH sequence (greeting and getting name) and is picked up by NEURAL_CHAT
    MOVIES_TO_CATEGORIES = auto()
    ONE_TURN_TO_WIKI_GF = auto()
    NEURALCHAT_TO_WIKI = auto()
    NEWS_TO_SPORTS = auto()
    PETS_TO_WIKI = auto()
