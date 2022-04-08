import logging
import random
from typing import Optional, Tuple, List
from chirpy.response_generators.neural_chat.treelets.abstract_treelet import Treelet
from chirpy.response_generators.neural_chat.state import State
from chirpy.response_generators.neural_chat.treelets.emotions.classify_mood import classify_utterance_mood, UserMood
from chirpy.core.response_generator_datatypes import PromptType

logger = logging.getLogger('chirpylogger')

HOW_ARE_YOU_FEELING_WITH_NAME = "I hope you don't mind me asking, how are you feeling, {name}?"
HOW_ARE_YOU_FEELING_WITHOUT_NAME = "I hope you don't mind me asking, how are you feeling?"

STARTER_QUESTIONS = {
    'NO_SHARE': "Oh hey, I just remembered, I wanted to check in with you.",
    'POS_OTHERS': "Oh hey, so, on another subject, I've noticed that a lot of people are feeling pretty positive today!",
    'POS_BOT': "Oh hey, so, on another subject, I wanted to say that I'm feeling pretty positive today!",
    'POS_BOT_STORY': "Oh hey, so, on another subject, I wanted to say I'm feeling pretty positive today! I just went for a walk outside, and it felt great to get some fresh air.",
    'NEG_OTHERS': "Oh hey, so, on another subject, I've noticed that a lot of people are feeling kind of down recently.",
    'NEG_BOT': "Oh hey, so, on another subject, I wanted to say that I've been feeling kind of down recently.",
    'NEG_BOT_STORY': "Oh hey, so, on another subject, I wanted to say that I've been feeling kind of down recently. I've been missing my friends a lot and finding it hard to focus.",
    'NEGOPT_OTHERS': "Oh hey, so, on another subject, I've noticed that a lot of people are feeling kind of down recently. But I think it's important to remember that things will get better.",
    'NEGOPT_BOT': "Oh hey, so, on another subject, I wanted to say that I've been feeling kind of down recently. But I think it's important to remember that things will get better.",
    'NEGOPT_BOT_STORY': "Oh hey, so, on another subject, I wanted to say that I've been feeling kind of down recently. But I think it's important to remember that things will get better. Just earlier today I took a walk outside and the fresh air helped me get some perspective.",
}

# Strategies for when the user says they're feeling good without elaborating further
GOOD_NO_ELAB_RESPONSE = "I'm so glad to hear you're feeling good!"
GOOD_NO_ELAB_STRATEGIES = {
    'PROBE_POS_TIPS': "I'd be interested to get some tips. What have you been doing that helps you stay in a good mood during these difficult times?",
    'PROBE_POS_EVENTS': "What's been happening?",
    'PROBE_POS_LIFE': "I'd love to hear, what are some of the good things in your life right now?",
    # 'MUSE': "Taking care of our emotions is so important.",
    # 'TRANSITION': '',
}

# Strategies for when the user says they're feeling neutral without elaborating further
NEUTRAL_NO_ELAB_RESPONSE = "I'm glad to hear that you're feeling OK."
NEUTRAL_NO_ELAB_STRATEGIES = {
    'PROBE_POS_TIPS': "I'd be interested to get some tips. What have you been doing that helps you manage in these difficult times?",
    # 'PROBE_NEG': "But if there's anything troubling you, you can tell me about it.",
    # 'MUSE': "Taking care of our emotions is so important.",
    # 'TRANSITION': '',
}

# Response for when the user says they're feeling bad without elaborating further
BAD_NO_ELAB_RESPONSE = "I'm so sorry to hear that you're having a tough time."
BAD_NO_ELAB_STRATEGIES = {
    'WHATS_GOING_ON': "What's going on?",
}

class EmotionsTreelet(Treelet):
    """Talks about user's current/recent emotions"""

    _launch_appropriate = False
    fallback_response = "I appreciate you sharing your feelings with me."

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

        # Get user name
        user_name = getattr(self.state_manager.user_attributes, 'name', None)  # str or None
        user_name_presence = 'USER_NAME_PRESENT' if user_name is not None else 'USER_NAME_NOT_PRESENT'  # 'USER_NAME_PRESENT' or 'USER_NAME_NOT_PRESENT'

        # Sample whether to use user's name
        use_name = random.choice(['USE_NAME', 'DONT_USE_NAME']) if user_name_presence == 'USER_NAME_PRESENT' else 'DONT_USE_NAME'

        # Sample which strategy to use
        strategy = random.choice(list(STARTER_QUESTIONS.keys()))

        # Compose starter question
        starter_question = "{} {}".format(STARTER_QUESTIONS[strategy], HOW_ARE_YOU_FEELING_WITH_NAME.format(name=user_name) if use_name=='USE_NAME' else HOW_ARE_YOU_FEELING_WITHOUT_NAME)
        logger.primary_info(f'Given that user_name_presence={user_name_presence}, we sampled strategy={strategy} and use_name={use_name}, so starter_question="{starter_question}"')
        return starter_question, [strategy, use_name, user_name_presence], PromptType.GENERIC


    @property
    def return_question_answer(self) -> str:
        """Gives a response to the user if they ask the "return question" to our starter question
                
        DEPRECATED -- No need w/ blenderbot"""
        return "Speaking for myself, I have good days and I have bad days."


    def optionally_get_nonneural_response(self, history: List[str]):
        """
        If we should give a non-neural response instead of calling remote module, give the response here.

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

        # Classify user mood
        user_utterance = history[-1]
        user_mood = classify_utterance_mood(user_utterance)

        # Give a response according to user mood and strategy
        if user_mood == UserMood.GOOD_NO_ELAB:
            strategy, response = random.choice(list(GOOD_NO_ELAB_STRATEGIES.items()))
            logger.primary_info(f'User gave {user_mood} response. Sampled strategy {strategy}.')
            return "{} {}".format(GOOD_NO_ELAB_RESPONSE, response), [user_mood], [strategy]
        elif user_mood == UserMood.NEUTRAL_NO_ELAB:
            strategy, response = random.choice(list(NEUTRAL_NO_ELAB_STRATEGIES.items()))
            logger.primary_info(f'User gave {user_mood} response. Sampled strategy {strategy}.')
            return "{} {}".format(NEUTRAL_NO_ELAB_RESPONSE, response), [user_mood], [strategy]
        elif user_mood == UserMood.BAD_NO_ELAB:
            strategy, response = random.choice(list(BAD_NO_ELAB_STRATEGIES.items()))
            logger.primary_info(f'User gave {user_mood} response. Sampled strategy {strategy}.')
            return "{} {}".format(BAD_NO_ELAB_RESPONSE, response), [user_mood], [strategy]
        elif user_mood == UserMood.OTHER:
            logger.primary_info(f'User gave {user_mood} response, so using DialoGPT to respond.')
            return None, [user_mood], []
        else:
            raise ValueError(user_mood)
