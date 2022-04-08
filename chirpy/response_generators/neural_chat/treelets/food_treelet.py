import logging
import random
from typing import Optional, Tuple, List

from chirpy.core.util import get_user_datetime
from chirpy.response_generators.neural_chat.treelets.abstract_treelet import Treelet
from chirpy.response_generators.neural_chat.state import State
from chirpy.core.response_generator_datatypes import PromptType
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.word_lists import INTENSIFIERS
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_MID, oneof, one_or_more_spacesep


logger = logging.getLogger('chirpylogger')


BREAKFAST_TRANSITION_PHRASES = [
    "I just noticed that it's breakfast time, my favorite time of day!",
    "My stomach is telling me that it's breakfast time right now.",
]

MORNING_TRANSITION_PHRASES = [
    "I hope you're having a wonderful morning.",
    "I hope your morning is going well.",
    "I hope you're having a lovely morning.",
]

LUNCHTIME_TRANSITION_PHRASES = [
    "I just noticed that it's lunch time, my favorite time of day!",
    "My stomach is telling me that it's lunch time right now.",
]

AFTERNOON_TRANSITION_PHRASES = [
    "I hope you're having a wonderful afternoon.",
    "I hope your afternoon is going well.",
    "I hope you're having a lovely afternoon.",
]

DINNER_TRANSITION_PHRASES = [
    "I just noticed that it's dinner time, my favorite time of day!",
    "My stomach is telling me that it's dinner time right now.",
]

EVENING_TRANSITION_PHRASES = [
    "I hope you're having a wonderful evening.",
    "I hope your evening is going well.",
    "I hope you're having a lovely evening.",
]

NON_TIME_SENSITIVE_STARTER_QUESTIONS = [
    "I was wondering if you could help me. I'm trying to be a more adventurous eater, but I'm not sure what new recipes I should try out. Do you have any recommendations for what I should cook at home?",
    "I think one of the best ways to get to know a person is via their stomach. What's one of your favorite things to eat?",
    "I think the key to a good mood is eating well. What's a food that always makes you feel good?",
]

HAVENT_EATEN_RESPONSE = "Oh no! I hope you find something good to eat soon! Perhaps instead, you can tell me about a meal you like to have often?"

HAVENT_EATEN_PHRASES = [
    "i (haven't|didn't|don't|have not|did not|do not)( (had|have|eaten|eat))?",
    "(haven't|didn't|don't|have not|did not|do not)( (had|have|eaten|eat))",
    "not (having|eating)",
    "not going to (eat|have)",
    "nothing",
    "i don't know",
    "not (breakfast|lunch|dinner)( )?time",
    "not time for (breakfast|lunch|dinner)",
    "i (forget|forgot)",
    "not sure",
    "no idea",
    "can't remember",
    "not ({} )*hungry".format(oneof(INTENSIFIERS + ['that'])),
]

class HaventEatenTemplate(RegexTemplate):
    slots = {
        'havent_eaten_phrase': HAVENT_EATEN_PHRASES,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{havent_eaten_phrase}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [

    ]
    negative_examples = [

    ]


class FoodTreelet(Treelet):
    """Talks about food"""

    _launch_appropriate = True
    fallback_response = "I enjoyed hearing about that. Food is one of life's great pleasures!"
    _starter_question_expected_type = ENTITY_GROUPS_FOR_EXPECTED_TYPE.food_related

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

        starter_questions = NON_TIME_SENSITIVE_STARTER_QUESTIONS

        # Get time-sensitive starter question
        date_time = get_user_datetime(self.state_manager.user_attributes.user_timezone)  # datetime.datetime / None

        if date_time:
            logger.info(f'As we have date_time={date_time}, {self.name} is getting the time-sensitive starter question.')
            time_sensitive_starter_question = self.get_timesensitive_starter_question(date_time)  # str or None
            if time_sensitive_starter_question:
                starter_questions.append(time_sensitive_starter_question)

        # Sample a starter question
        starter_question = random.choice(starter_questions)
        logger.info("{} sampled starter_question='{}' from:\n{}".format(self.name, starter_question, '\n'.join(starter_questions)))

        # Use a different transition phrase depending on whether it's used for launch sequence
        if for_launch:
            starter_question = "So, {}".format(starter_question)
        else:
            starter_question = "Hmm, so, on another topic. {}".format(starter_question)

        return starter_question, [], PromptType.GENERIC

    def get_timesensitive_starter_question(self, date_time) -> Optional[str]:
        logger.info(f'Getting time-sensitive starter question for {self.name} with date_time={date_time}')
        if 5 <= date_time.hour < 9:  # 5am-9am
            return "{} {}".format(random.choice(BREAKFAST_TRANSITION_PHRASES), "What are you having for breakfast today?")
        if 9 <= date_time.hour < 12:  # 9am-12am
            return "{} {}".format(random.choice(MORNING_TRANSITION_PHRASES), "What did you have for breakfast today?")
        elif 12 <= date_time.hour < 14:  # 12am-2pm
            return "{} {}".format(random.choice(LUNCHTIME_TRANSITION_PHRASES), "What are you having for lunch today?")
        elif 14 <= date_time.hour < 17:  # 2pm-5pm
            return "{} {}".format(random.choice(AFTERNOON_TRANSITION_PHRASES), "What did you have for lunch today?")
        elif 17 <= date_time.hour < 20:  # 5pm-8pm
            return "{} {}".format(random.choice(DINNER_TRANSITION_PHRASES), "What are you having for dinner today?")
        elif 20 <= date_time.hour:  # 8pm-midnight
            return "{} {}".format(random.choice(EVENING_TRANSITION_PHRASES), "What did you have for dinner today?")
        else:
            return None

    @property
    def return_question_answer(self) -> str:
        """Gives a response to the user if they ask the "return question" to our starter question
                
        DEPRECATED -- No need w/ blenderbot"""
        return "Oh, I love eating Mexican food like quesadillas and tacos. I even love to tacobout them, haha!"

    def optionally_get_nonneural_response(self, history: List[str]):
        """
        If we should give a non-neural response instead of calling DialoGPT, give the response here.

        Inputs:
            history: odd-length list of strings, starting and ending with user utterances

        Returns:
            non_neural_response: str or None.
            user_labels: any additional labels that should be applied to the user utterance on this turn
            bot_labels: any additional labels that should be applied to the bot utterance on this turn
        """
        # If the user isn't responding to the starter_q on this turn, return None
        if len(history) != 3:  # ['', starter_q, user_response]
            return None, [], []

        # If we detected an entity, let GPT respond
        if self.state_manager.current_state.entity_tracker.cur_entity is not None:
            return None, [], []

        # If user is saying they haven't eaten, give the scripted response
        if HaventEatenTemplate().execute(history[-1]) is not None:
            logger.primary_info(f"User utterance '{history[-1]}' matches HaventEatenTemplate so using scripted response")
            return HAVENT_EATEN_RESPONSE, ['HAVENT_EATEN'], []

        # Otherwise return nothing
        return None, [], []
