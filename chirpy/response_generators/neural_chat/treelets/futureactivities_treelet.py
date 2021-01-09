import logging
from typing import Optional, Tuple, List

from chirpy.core.util import get_user_datetime, get_user_dayofweek
from chirpy.response_generators.neural_chat.treelets.abstract_treelet import Treelet
from chirpy.response_generators.neural_chat.state import State
from chirpy.core.response_generator_datatypes import PromptType

logger = logging.getLogger('chirpylogger')


class FutureActivitiesTreelet(Treelet):
    """Talks about activities in the future (after today)"""

    _launch_appropriate = False
    fallback_response = "I hope it goes well for you!"

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

        prompt_type = PromptType.GENERIC

        # Get the user's datetime and day of the week
        date_time = get_user_datetime(self.state_manager.user_attributes.user_timezone)  # datetime.datetime / None
        day_of_week = get_user_dayofweek(self.state_manager.user_attributes.user_timezone)  # str / None

        if day_of_week in ['Tuesday', 'Wednesday', 'Thursday']:
            return "Hmm, so, on another topic. It might just be {day_of_week}, but I feel like it's been a long week so far! I can't wait for the weekend. " \
                   "Do you have any plans for the weekend?".format(day_of_week=day_of_week), [], prompt_type
        elif day_of_week in ['Friday']:
            return "Oh hey, sorry to change the subject, but I just remembered something awesome. It's the weekend soon! Do you have any plans for the weekend?", [], prompt_type
        elif date_time and (21 <= date_time.hour or date_time.hour < 2):  # 9pm-2am
            return "Hmm, so, on another subject, I just noticed that it's getting near by bedtime. Before I go to bed I like to think about something I'm looking forward to tomorrow. " \
                   "What about you, are you doing anything nice tomorrow?", [], prompt_type
        else:
            return "Anyway, there's actually something unrelated I wanted to ask you about. I think it's been tough for everyone to adjust to how things are right now. " \
                   "I try to remind myself that one day not too long from now, things will go back to normal. " \
                   "What are you looking forward to doing once this is over?", [], prompt_type

    @property
    def return_question_answer(self) -> str:
        """Gives a response to the user if they ask the "return question" to our starter question"""
        return "I'm hoping I'll be able to hang out with my friends, but for now it will probably need to be remotely."