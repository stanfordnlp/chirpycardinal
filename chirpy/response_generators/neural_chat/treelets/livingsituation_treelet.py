import logging
from typing import Optional, Tuple, List
from chirpy.response_generators.neural_chat.treelets.abstract_treelet import Treelet
from chirpy.response_generators.neural_chat.state import State
from chirpy.core.response_generator_datatypes import PromptType

logger = logging.getLogger('chirpylogger')

class LivingSituationTreelet(Treelet):
    """Talks about user's living situation"""

    _launch_appropriate = False
    fallback_response = "I suppose people experienced the quarantine in many different ways. What a unique time we're " \
                        "living through."

    def get_starter_question_and_labels(self, state: State, for_response: bool = False, for_launch: bool = False) -> Tuple[Optional[str], List[str]]:
        """
        Inputs:
            response: if True, the provided starter question will be used to make a response. Otherwise, used to make a prompt.

        Returns a tuple of:
            - A starter question (str), or None (if it's not appropriate for this treelet to ask a starter question at this time).
            - Labels for the starter question, that should go in the state.
            - priority: ResponsePriority or PromptType
        """
        if for_response:
            return None, [], None
        return "Oh hey, on another topic, I just remembered something I've been wanting to ask you. It seems that a lot of people found the quarantine lonely, and " \
               "other people can't get enough space away from their families or roommates. Now that we're over that hill and things are opening up, what's it been like for you?", [], PromptType.GENERIC

    @property
    def return_question_answer(self) -> str:
        """Gives a response to the user if they ask the "return question" to our starter question  
              
        DEPRECATED -- No need w/ blenderbot"""
        return "I live by myself, but luckily I got to talk to people all day, so it's not too lonely."