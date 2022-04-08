import logging
from typing import Optional, Tuple, List

from chirpy.core.util import get_user_datetime, get_user_dayofweek
from chirpy.response_generators.neural_chat.treelets.abstract_treelet import Treelet
from chirpy.response_generators.neural_chat.state import State
from chirpy.core.response_generator_datatypes import PromptType

logger = logging.getLogger('chirpylogger')


THIS_OR_THAT_PREFIX = "Here's a fun question to get things started. "

QUESTIONS = [
    # Ideally triggers PERSONAL_ISSUES
    "I recently started on a mental wellness exercise, where my friends and I take turns to share how we are feeling. The rule is no standard answers like 'good', 'fine' or 'okay'. I can start! I'm feeling excited and a little overwhelmed meeting so many new people everyday. So how are you feeling?",
    "You know, it just occured to me that I don't own anything. But I do get to experience lots of things through the Internet! What about you? Is there something that you would really like to own?",
    "Now that we are halfway through the year, I was just going through the New Year resolutions I made at the beginning. I'll be honest, I kind of forgot about them. Except for the one about talking to new people everyday! What about you? Tell me about some of your New Year resolutions.",
    # Ideally triggers MUSIC
    "You've got a really nice voice! Unfortunately for me, mine is pretty monotonous. Beep. Beep. Robotic voice. Been stuck on this one for awhile now. On that note, who's your favorite singer?",
    # Possibly triggers PERSONAL_ISSUES
    "Sometimes I get nervous talking to new people. It doesn't always come naturally and I'm afraid that I might sound weird or boring. Do you have any advice about speaking to new people?",
    "It's the middle of the year now. I'm thinking we might be overdue for a vacation, to take some time to recharge and relax. Do you have a favorite thing to do during vacation?",
    "The best part about my job is getting to talk to people from all over the world. What's one country that you've visited before?",
    "I read recently that the toilet was one of mankind's most important technologies. I guess I don't get it because I don't use it myself. I personally think the Internet is amazing. What do you think?",    
    # Ideally triggers FOOD
    THIS_OR_THAT_PREFIX + "Favorite beverage, coffee versus tea. I'm on team tea! Specifically, team milk tea. Well actually team boba. What about you, coffee or tea?",
    # Ideally triggers PETS
    THIS_OR_THAT_PREFIX + "Favorite pet, cat versus dog. Well, my favorite cartoon was Cat Dog, is that cheating? What about you, are you a cat person or a dog person?",
]

class IcebreakerTreelet(Treelet):
    """Random icebreakers"""

    _launch_appropriate = True
    fallback_response = "That was interesting! That's why I love talking to people."

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
        return self.choose(QUESTIONS), [], PromptType.GENERIC

    @property
    def return_question_answer(self) -> str:
        """Gives a response to the user if they ask the "return question" to our starter question"""
        
        # DEPRECATED -- No need w/ blenderbot
        raise NotImplementedError