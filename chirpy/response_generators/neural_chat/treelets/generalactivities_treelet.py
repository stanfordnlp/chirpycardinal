import logging
from typing import Optional, Tuple, List
from chirpy.response_generators.neural_chat.treelets.abstract_treelet import Treelet
from chirpy.response_generators.neural_chat.state import State
from chirpy.core.response_generator_datatypes import PromptType

logger = logging.getLogger('chirpylogger')

STARTER_QUESTIONS = [
    "So, changing the subject a little. Recently, I've been trying meditation to help me relax during this stressful time. What do you like to do to relax?",
    "Um, on another subject. You know, I was reading earlier today that staying busy helps people stay calm and healthy during stressful times. What do you like to do to keep busy?",
    # "Oh, by the way, I read recently that staying active helps people stay calm and healthy during stressful times. What have you been doing to stay active?",  # too easily answered with "nothing"
    # "Oh, by the way, I read recently that keeping in contact with your friends and family helps people stay calm and healthy during stressful times. Have you been able to find ways to spend time with friends and family?",  # too easily answered with "no"
]

class GeneralActivitiesTreelet(Treelet):
    """Talks about general activities and interests"""

    _launch_appropriate = False
    fallback_response = "Thanks for telling me about that, maybe I'll give it a try."

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
        return self.choose(STARTER_QUESTIONS), [], PromptType.GENERIC

    @property
    def return_question_answer(self) -> str:
        """Gives a response to the user if they ask the "return question" to our starter question
        
        DEPRECATED -- No need w/ blenderbot"""
        return "I like knitting. It keeps my mind and fingers occupied but it's also super relaxing."
