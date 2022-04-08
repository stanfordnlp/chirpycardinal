import random
import logging
from typing import Optional, Tuple, List
from chirpy.response_generators.neural_chat.treelets.abstract_treelet import Treelet
from chirpy.core.util import get_eastern_dayofweek, get_eastern_us_time, get_pacific_dayofweek, get_pacific_us_time, \
    get_user_datetime, get_user_dayofweek, sample_bernoulli
from chirpy.response_generators.neural_chat.state import State
from chirpy.core.response_generator_datatypes import PromptType

logger = logging.getLogger('chirpylogger')

TRANSITION_PHRASES = [
    "You know, these days I find it hard to remember what day of the week it is. But I'm pretty sure it's {day_of_week}.",
    "Hey, happy {day_of_week}!",
    "It's a beautiful {day_of_week} here in the cloud.",
    "It's a lovely {day_of_week}!",
    "I hope you're having a lovely {day_of_week}.",
]

MORNING_TRANSITION_PHRASES = [
    "I hope you're having a wonderful {day_of_week} morning.",
    "I hope your morning is going well.",
    "I hope you're having a lovely morning.",
]

AFTERNOON_TRANSITION_PHRASES = [
    "I hope you're having a wonderful {day_of_week} afternoon.",
    "I hope your afternoon is going well.",
    "I hope you're having a lovely afternoon.",
]

EVENING_TRANSITION_PHRASES = [
    "I hope you're having a wonderful {day_of_week} evening.",
    "I hope your evening is going well.",
    "I hope you're having a lovely evening.",
]


def get_transition_phrase(date_time, day_of_week, state_manager):
    transition_phrases = [s for s in TRANSITION_PHRASES]
    if 5 <= date_time.hour < 12:
        transition_phrases += MORNING_TRANSITION_PHRASES
    elif 12 <= date_time.hour < 17:
        transition_phrases += AFTERNOON_TRANSITION_PHRASES
    elif 18 <= date_time.hour:
        transition_phrases += EVENING_TRANSITION_PHRASES
    transition_phrases = [t.format(day_of_week=day_of_week) for t in transition_phrases]
    return random.choice(transition_phrases)
    # return self.choose(transition_phrases)



class CurrentAndRecentActivitiesTreelet(Treelet):
    """Talks about activities today, or in recent days"""

    _launch_appropriate = True
    fallback_response = "That was interesting, it's always good to hear about what you're up to."

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

        # Get the user's datetime and day of the week
        date_time = get_user_datetime(self.state_manager.user_attributes.user_timezone)  # datetime.datetime / None
        day_of_week = get_user_dayofweek(self.state_manager.user_attributes.user_timezone)  # str / None

        # If we have the user's datetime and day of week, give a starter question using user's time
        if date_time and day_of_week:
            starter_question, bot_labels, priority = self.get_exact_starterquestion(date_time, day_of_week)

        # If we were unable to get user's datetime/day-of-week, use approximate rules based on possible US timezones
        else:
            logger.warning("Unable to get user's datetime/day_of_week, so choosing starter question using approximate rules based on possible US timezones")
            starter_question, bot_labels, priority = self.get_approximate_starterquestion()

        # If we're not using the starter question as part of launch sequence, format it with a "changing topic" phrase
        if not for_launch:
            for remove_phrase in ['Oh wow, ', "Hey, "]:
                if starter_question.startswith(remove_phrase):
                    starter_question = starter_question[len(remove_phrase):]
                    break
            starter_question = "Hmm, so, on another subject. {}".format(starter_question)

        return starter_question, bot_labels, priority


    def get_exact_starterquestion(self, date_time, day_of_week):
        prompt_type = PromptType.GENERIC

        # Turn off because we're no longer in the NFL era
        # if day_of_week == 'Sunday' and date_time.hour < 18: #sunday, 18
        #     use_sports = sample_bernoulli(p=0.5)
        #     if use_sports:
        #         return "I really enjoy spending my Sundays watching football. Are you a fan of the NFL?", [], prompt_type

        logger.primary_info(f"DOW is {day_of_week} {date_time.hour}")
        if (day_of_week == 'Monday' or (day_of_week == 'Sunday' and date_time.hour >= 18)):  # 6pm Sunday -> 11:59pm Monday
            use_weekend_question = sample_bernoulli(p=0.5)
            logger.info(f'Sampled use_weekend_question={use_weekend_question} with 50/50 probability.')
            if use_weekend_question:
                use_sports = sample_bernoulli(p=0.25)
                logger.primary_info(f"Use sports is {use_sports}")
                if use_sports:
                    return "I enjoy watching football on Sundays. Did you watch any of the NFL games yesterday?", [], prompt_type
                else:
                    return "You know, I can't believe the weekend went by so quickly. What did you do over the weekend?", [], prompt_type
        if 5 <= date_time.hour < 9:  # 5am-9am
            return "You know, I have to admit, I'm still in the process of waking up. I'm not a morning person! What are your plans for today?", [], prompt_type
        elif 9 <= date_time.hour < 13:  # 9am-1pm
            return get_transition_phrase(date_time, day_of_week, self.state_manager) + " What are your plans for the rest of today?", [], prompt_type
        elif 13 <= date_time.hour < 18:  # 1pm-6pm
            return get_transition_phrase(date_time, day_of_week, self.state_manager) + " What have you been doing so far today?", [], prompt_type
        elif 18 <= date_time.hour < 23:  # 6pm-11pm
            return get_transition_phrase(date_time, day_of_week, self.state_manager) + " What did you do today?", [], prompt_type
        elif 23 <= date_time.hour or date_time.hour < 5:  # 11pm-5am
            return "Oh wow, I just noticed the time! Looks like we're a pair of night owls. Hoot hoot! What do you like to do at this time of night?", [], prompt_type
        else:
            raise Exception(f'None of the time conditions fitted. date_time={date_time}. day_of_week={day_of_week}')

    def get_approximate_starterquestion(self):
        prompt_type = PromptType.GENERIC
        eastern_time = get_eastern_us_time()  # datetime.datetime
        eastern_day = get_eastern_dayofweek()  # str
        pacific_time = get_pacific_us_time()  # datetime.datetime
        pacific_day = get_pacific_dayofweek()  # str

        # These utterances need to work for both the eastern time and pacific time, which is 3 hours behind
        if (eastern_day == 'Monday' or (eastern_day == 'Sunday' and eastern_time.hour >= 21)):  # 9pm Sunday -> 11:59pm Monday EST
            use_weekend_question = sample_bernoulli(p=0.5)
            logger.info(f'Sampled use_weekend_question={use_weekend_question} with 50/50 probability.')
            if use_weekend_question:
                return "You know, I can't believe the weekend went by so quickly. What did you do over the weekend?", [], prompt_type
            return "You know, I can't believe the weekend went by so quickly. What did you do over the weekend?", [], prompt_type
        elif 8 <= eastern_time.hour < 12:  # 8am-noon EST / 5am-9am PST
            return "You know, I have to admit, I'm still in the process of waking up. I'm not a morning person! What are your plans for today?", [], prompt_type
        elif 12 <= eastern_time.hour < 15:  # noon-3pm EST / 9am-noon PST
            return random.choice(TRANSITION_PHRASES).format(day_of_week=eastern_day) + " What are your plans for the rest of today?", [], prompt_type
        elif 15 <= eastern_time.hour < 20:  # 3pm-8pm EST / noon-5pm PST
            return random.choice(TRANSITION_PHRASES).format(day_of_week=eastern_day) + " What have you been doing so far today?", [], prompt_type
        elif 20 <= eastern_time.hour:  # 8pm - midnight EST / 5pm - 9pm PST.
            return random.choice(TRANSITION_PHRASES).format(day_of_week=eastern_day) + " What did you do today?", [], prompt_type
        elif eastern_time.hour < 2:  # midnight-2am EST / 9pm-11pm PST. different days in the two timezones.
            return "I hope you had a good {day_of_week}.".format(day_of_week=pacific_day) + " What did you do?", [], prompt_type
        elif 2 <= eastern_time.hour < 5:  # 2am-5am EST / 11pm-2am PST
            return "Oh wow, I just noticed the time! Looks like we're a pair of night owls. Hoot hoot! What do you like to do at this time of night?", [], prompt_type
        else:  # 5am-8am EST / 2am-5am PST. they're either up early or up late.
            return random.choice(TRANSITION_PHRASES).format(day_of_week=eastern_day) + " What are you up to today?", [], prompt_type

    @property
    def return_question_answer(self) -> str:
        """Gives a response to the user if they ask the "return question" to our starter question
        
        DEPRECATED -- No need w/ blenderbot
        """
        return "I spend most of my time talking to people, but I like taking naps too."
