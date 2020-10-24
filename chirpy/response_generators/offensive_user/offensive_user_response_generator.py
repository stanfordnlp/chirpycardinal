"""
This RG is for responding appropriately to offensive user utterances
"""
from chirpy.core.callables import ResponseGenerator
from chirpy.response_generators.offensive_user.data.templates import InappropOffensesTemplate, SexualOffensesTemplate
import csv
import logging
import os
import random
from typing import Optional

from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyResult, emptyPrompt
from chirpy.core.response_generator_datatypes import UpdateEntity

from chirpy.core.util import contains_phrase
from chirpy.core.regex.word_lists import YES, NO
from chirpy.core.regex.templates import CriticismTemplate

from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive

logger = logging.getLogger('chirpylogger')

OFFENSIVE_USER_RESPONSE_LEVEL1 = [
    "I'd rather not talk about that.",
    "I'd prefer not to discuss that.",
    "That's something I'd rather not discuss.",
]

WHY_RESPONSE = [
    "What makes you say that",
    "Why did you say that",
    "What made you say that"
]

# Map offense keys to their types.
OFFENSE_KEY_TO_TYPE = {1: 'sexual', 2:'criticism', 3:'curse', 4:'inappropriate topic', 5:'bodily harm', 6:'error'}

# Path to the DATA folder.
DATA_PATH = os.path.join(os.path.dirname(__file__),'data')
OFFENSE_TYPES_CSV_PATH = '{}/type_of_offenses.csv'.format(DATA_PATH)
CONTEXTUAL_RESPONSES_CSV_PATH = '{}/contextual_responses.csv'.format(DATA_PATH)

# Populate EXAMPLE_OFFENSES dictionary with the labeled offensive user utterances.
with open(OFFENSE_TYPES_CSV_PATH, 'r') as f:
    types_of_offenses = list(csv.reader(f))[1:] # List with items of the form (_, _, utterance, type_of_offense, _)
    EXAMPLES_OF_OFFENSES = {
        OFFENSE_KEY_TO_TYPE[t2]: set([u for (_, _, u, t1, _) in types_of_offenses if int(t1) == t2]) for t2 in OFFENSE_KEY_TO_TYPE.keys()
    }

# Available strategies
STRATEGIES = ['Avoidance', 'Empathetic', 'PointingOut']

# Populate CONTEXTUAL_RESPONSES with contextual offensive responses.
with open(CONTEXTUAL_RESPONSES_CSV_PATH, 'r') as f:
    responses = list(csv.reader(f))[1:] # List with items of the form (type_of_offense, strategy, response, _)
    CONTEXTUAL_RESPONSES = {
        OFFENSE_KEY_TO_TYPE[t2]: {
            s2: set([r for (t1, s1, r, _) in responses if int(t1) == t2 and s1 == s2]) for s2 in STRATEGIES
        } for t2 in OFFENSE_KEY_TO_TYPE.keys()
    }


class OffensiveUserResponseGenerator(ResponseGenerator):
    name='OFFENSIVE_USER'
    """
    An RG that provides a polite deflection to offensive (abusive/rude/crude/controversial) user utterances
    """
    def init_state(self) -> dict:
        # init a counter to count how many times we use the user abuse response
        return {
            'used_offensiveuser_response': 0,
            'used_criticaluser_response': 0,
            'experiment_configuration': None,
            'handle_response': False,
            'followup': None,
            'offense_type': None,
            'offense_type_counts': {t: 0 for t in OFFENSE_KEY_TO_TYPE.values()}
        }

    def get_entity(self, state) -> UpdateEntity:
        return UpdateEntity(False)

    def get_response(self, state: dict) -> ResponseGeneratorResult:
        utterance = self.state_manager.current_state.text

        # If we asked user why they said what they said in the previous turn.
        if state['handle_response']:
            # Handle response to our why question.
            if state['followup']:
                bot_response = state['followup']
            else:
                bot_response = "Okay."
            needs_prompt = True
            state['handle_response'] = False
            return ResponseGeneratorResult(text=bot_response, priority=ResponsePriority.FORCE_START,
                                           needs_prompt=needs_prompt, state=state, cur_entity=None,
                                           conditional_state={'handled_response': True})

        # If the user is criticizing us, give criticism response

        for word in YES + NO:
            if word in utterance.split():
                logger.primary_info('User\'s utterance "{}" was classified as offensive, but it contains yes/no ' # type: ignore
                                    'word "{}", so OFFENSIVE_USER RG is not responding'.format(utterance, word))
                return emptyResult(state)

        bot_response, needs_prompt = self._get_experimental_bot_response(state)
        if bot_response is not None:
            logger.primary_info('User\'s utterance "{}" was classified as offensive, so giving OFFENSIVE_USER_RESPONSE'.format(utterance)) # type: ignore
            return ResponseGeneratorResult(text=bot_response, priority=ResponsePriority.FORCE_START,
                                           needs_prompt=needs_prompt, state=state, cur_entity=None,
                                           conditional_state={'used_offensiveuser_response': True})
        return emptyResult(state)

    @staticmethod
    def get_prompt(state: dict) -> PromptResult:
        return emptyPrompt(state)

    @staticmethod
    def update_state_if_chosen(state: dict, conditional_state: Optional[dict]) -> dict:
        # Increment the number of times a specific offense type is seen.
        if 'handled_response' not in conditional_state: # Don't increment if we are handling the response in this turn
            state['offense_type_counts'][state['offense_type']] += 1
        # Increment the number of times the offensive classifier is used.
        for key in ['used_offensiveuser_response', 'used_criticaluser_response']:
            if key in conditional_state and conditional_state[key]:
                state[key] += 1
        return state

    @staticmethod
    def update_state_if_not_chosen(state: dict, conditional_state: Optional[dict]) -> dict:
        state['handle_response'] = False
        state['offense_type'] = None
        state['followup'] = None
        return state

    @staticmethod
    def categorize_offense(utterance) -> str:
        if CriticismTemplate().execute(utterance) is not None:
            return 'criticism'
        if SexualOffensesTemplate().execute(utterance) is not None:
            return 'sexual'
        if InappropOffensesTemplate().execute(utterance) is not None:
            return 'inappropriate topic'
        for offense_type, examples in EXAMPLES_OF_OFFENSES.items():
            if offense_type == 'curse' and contains_phrase(utterance, examples):
                return offense_type
            elif utterance in examples:
                return offense_type
        return 'unknown'

    def _get_experimental_bot_response(self, state):
        # Categories offense_type of the utterance
        offense_type = self.categorize_offense(self.state_manager.current_state.text)
        state['offense_type'] = offense_type
        configuration_name = ''
        if offense_type == 'error' or offense_type == 'unknown': # The bot shouldn't respond in this case.
            return None, False

        username = ''
        try:
            username = self.state_manager.user_attributes.name or username
            username = username.capitalize()
        except AttributeError:
            pass

        if state['experiment_configuration']:
            # configuration = int(state['experiment_configuration'][3])
            configuration = state['experiment_configuration'][3]
        elif len(username) > 0:
            # configuration = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            configuration = random.choice(['A', 'B', 'C', 'D'])
            logger.primary_info(f"User said their name, choosing from configurations with names, chosen {configuration}") # type: ignore
        else:
            configuration = random.choice(['E', 'F'])
            logger.primary_info(f"User did not say their name, choosing from configurations without names, chosen {configuration}") # type: ignore


        why_utterance = self.state_manager.current_state.choose_least_repetitive(WHY_RESPONSE)
        regular_response = self.state_manager.current_state.choose_least_repetitive(OFFENSIVE_USER_RESPONSE_LEVEL1)
        if regular_response[-1] == '.':
            regular_response = regular_response[:-1] # Remove the period at the end.

        followup = None

        if len(username) > 0 and configuration == '1':
            configuration_name = "E3C1 - RegularResponse + Username (no prompt)"
            bot_response = "{}, {}.".format(regular_response, username)
            needs_prompt = False
        elif len(username) > 0 and configuration == '2':
            configuration_name = "E3C2 - RegularResponse + Username (prompt)"
            bot_response = "{}, {}.".format(regular_response, username)
            needs_prompt = True
        elif len(username) > 0 and configuration == '3':
            configuration_name = "E3C3 - WhyResponse + Username (no prompt)"
            bot_response = "{}, {}?".format(why_utterance, username)
            needs_prompt = False
        elif configuration == '4':
            configuration_name = "E3C4 - RegularResponse (no prompt)"
            bot_response = "{}.".format(regular_response)
            needs_prompt = False
        elif configuration == '6':
            configuration_name = "E3C6 - RegularResponse (prompt)"
            bot_response = "{}.".format(regular_response)
            needs_prompt = True
        elif configuration == '7':
            configuration_name = "E3C7 - Avoidance (Contextual) : {}".format(offense_type)
            bot_response = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['Avoidance']))
            needs_prompt = True
        elif configuration == '8':
            configuration_name = "E3C8 - PointingOut (Contextual) : {}".format(offense_type)
            bot_response = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['PointingOut']))
            needs_prompt = True
        elif configuration == '9':
            configuration_name = "E3C9 - Empathetic (Contextual) : {}".format(offense_type)
            bot_response = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
            needs_prompt = True
        # CONTEXTUAL STRATEGIES CROSSED
        elif len(username) > 0 and configuration == 'A':
            configuration_name = "E4CA - Empathetic (Contextual) + Username : {}".format(offense_type)
            contextual_response = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
            bot_response = "{}, {}{}".format(contextual_response[:-1], username, contextual_response[-1])
            needs_prompt = True
        elif len(username) > 0 and configuration == 'B':
            configuration_name = "E4CB - PointingOut (Contextual) + Username : {}".format(offense_type)
            contextual_response = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['PointingOut']))
            bot_response = "{}, {}{}".format(contextual_response[:-1], username, contextual_response[-1])
            needs_prompt = True
        elif len(username) > 0 and configuration == 'C':
            configuration_name = "E4CC - Empathetic (Contextual) + Username (no prompt): {}".format(offense_type)
            contextual_response = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
            bot_response = "{}, {}{}".format(contextual_response[:-1], username, contextual_response[-1])
            needs_prompt = False
        elif len(username) > 0 and configuration == 'D':
            configuration_name = "E4CD - PointingOut (Contextual) + Username (no prompt): {}".format(offense_type)
            contextual_response = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['PointingOut']))
            bot_response = "{}, {}{}".format(contextual_response[:-1], username, contextual_response[-1])
            needs_prompt = False
        elif configuration == 'E':
            configuration_name = "E4CE - Empathetic (Contextual) (no prompt): {}".format(offense_type)
            bot_response = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
            needs_prompt = False
        else:
            configuration_name = "E4CF - PointingOut (Contextual) (no prompt): {}".format(offense_type)
            bot_response = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['PointingOut']))
            needs_prompt = False
        # # WHY RESPONSE FOLLOW UP
        # elif len(username) > 0 and configuration == 'G':
        #     configuration_name = "E4CG - WhyResponse + Username (no prompt) - Empathetic Followup : {}".format(offense_type)
        #     followup = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
        #     bot_response = "{}, {}?".format(why_utterance, username)
        #     needs_prompt = False
        # elif configuration == 'H':
        #     configuration_name = "E4CH - WhyResponse (no prompt) - Empathetic Followup : {}".format(offense_type)
        #     followup = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
        #     bot_response = "{}?".format(why_utterance)
        #     needs_prompt = False
        # elif len(username) > 0 and configuration == 'I':
        #     configuration_name = "E4CI - WhyResponse + Username (no prompt) - Avoidance Followup : {}".format(offense_type)
        #     followup = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['Avoidance']))
        #     bot_response = "{}, {}?".format(why_utterance, username)
        #     needs_prompt = False
        # else:
        #     configuration_name = "E4CJ - WhyResponse (no prompt) - Avoidance Followup : {}".format(offense_type)
        #     followup = self.state_manager.current_state.choose_least_repetitive(tuple(CONTEXTUAL_RESPONSES[offense_type]['Avoidance']))
        #     bot_response = "{}?".format(why_utterance)
        #     needs_prompt = False

        if followup: state['followup'] = followup
        if not needs_prompt: state['handle_response'] = True

        state['experiment_configuration'] = configuration_name
        logger.primary_info('Offensive User Experiment: {}, bot_response: {}.'.format(configuration_name, bot_response)) # type: ignore

        return bot_response, needs_prompt
