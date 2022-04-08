"""
This RG is for responding appropriately to offensive user utterances
"""
from chirpy.core.response_generator import ResponseGenerator
import logging
import random
from typing import Optional


from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyResult, emptyPrompt
from chirpy.core.response_generator_datatypes import UpdateEntity

from chirpy.core.regex.word_lists import YES, NO

from chirpy.response_generators.offensive_user.offensive_user_helpers import *
from chirpy.response_generators.offensive_user.state import *
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.response_generator.response_type import ResponseType

logger = logging.getLogger('chirpylogger')


class OffensiveUserResponseGenerator(ResponseGenerator):
    name='OFFENSIVE_USER'
    def __init__(self, state_manager):
        super().__init__(state_manager, can_give_prompts=False, state_constructor=State,
                         conditional_state_constructor=ConditionalState)
    """
    An RG that provides a polite deflection to offensive (abusive/rude/crude/controversial) user utterances
    """
    def handle_default_post_checks(self):
        state, utterance, response_types = self.get_state_utterance_response_types()

        if state.handle_response:
            if state.followup:
                bot_response = state.followup
            else:
                bot_response = "Okay."
            needs_prompt = True
            return ResponseGeneratorResult(text=bot_response, priority=ResponsePriority.FORCE_START,
                                           needs_prompt=needs_prompt, state=state, cur_entity=None,
                                           conditional_state=ConditionalState(handle_response=False,
                                                                              handled_response=True))

        # If the user is criticizing us, give criticism response
        if ResponseType.YES in response_types or ResponseType.NO in response_types:
            logger.primary_info(
                f'User\'s utterance "{utterance}" contains yes/no word, so OFFENSIVE_USER RG is not responding')
            return self.emptyResult()

        bot_response, needs_prompt = self._get_experimental_bot_response(state)
        if bot_response is not None:
            logger.primary_info(
                f'User\'s utterance "{utterance}" was classified as offensive, so giving OFFENSIVE_USER_RESPONSE') # type: ignore
            return ResponseGeneratorResult(text=bot_response, priority=ResponsePriority.FORCE_START,
                                           needs_prompt=needs_prompt, state=state, cur_entity=None,
                                           conditional_state=ConditionalState(used_offensiveuser_response=True))

    def update_state_if_chosen(self, state: State, conditional_state: Optional[ConditionalState]):
        state = super().update_state_if_chosen(state, conditional_state)
        if state.handled_response is not True:
            state.offense_type_counts[state.offense_type] += 1
        if state.used_criticaluser_response is True:
            state.used_criticaluser_response_count += 1
        if state.used_offensiveuser_response is True:
            state.used_offensiveuser_response_count += 1
        return state

    # # @staticmethod
    # # def update_state_if_chosen(state: dict, conditional_state: Optional[dict]) -> dict:
    #     # Increment the number of times a specific offense type is seen.
    #     if 'handled_response' not in conditional_state: # Don't increment if we are handling the response in this turn
    #         state['offense_type_counts'][state['offense_type']] += 1
    #     # Increment the number of times the offensive classifier is used.
    #     for key in ['used_offensiveuser_response', 'used_criticaluser_response']:
    #         if key in conditional_state and conditional_state[key]:
    #             state[key] += 1
    #     return state

    def update_state_if_not_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> BaseState:
        state = super().update_state_if_not_chosen(state, conditional_state)
        state.handle_response = False
        state.offense_type = None
        state.followup = None
        return state

    def _get_experimental_bot_response(self, state):
        # Categories offense_type of the utterance
        offense_type = categorize_offense(self.state_manager.current_state.text)
        state.offense_type = offense_type
        if offense_type == 'error' or offense_type == 'unknown': # The bot shouldn't respond in this case.
            return None, False

        username = ''
        try:
            username = self.state_manager.user_attributes.name or username
            username = username.capitalize()
        except AttributeError:
            pass

        if state.experiment_configuration:
            # configuration = int(state['experiment_configuration'][3])
            configuration = state.experiment_configuration[3]
        elif len(username) > 0:
            # configuration = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            configuration = random.choice(['A', 'B', 'C', 'D'])
            logger.primary_info(f"User said their name, choosing from configurations with names, chosen {configuration}") # type: ignore
        else:
            configuration = random.choice(['E', 'F'])
            logger.primary_info(f"User did not say their name, choosing from configurations without names, chosen {configuration}") # type: ignore

        why_utterance = self.choose(WHY_RESPONSE)
        regular_response = self.choose(OFFENSIVE_USER_RESPONSE_LEVEL1)
        if regular_response[-1] == '.':
            regular_response = regular_response[:-1] # Remove the period at the end.

        followup = None

        if len(username) > 0 and configuration == '1':
            configuration_name = "E3C1 - RegularResponse + Username (no prompt)"
            bot_response = f"{regular_response}, {username}."
            needs_prompt = False
        elif len(username) > 0 and configuration == '2':
            configuration_name = "E3C2 - RegularResponse + Username (prompt)"
            bot_response = f"{regular_response}, {username}."
            needs_prompt = True
        elif len(username) > 0 and configuration == '3':
            configuration_name = "E3C3 - WhyResponse + Username (no prompt)"
            bot_response = f"{why_utterance}, {username}?"
            needs_prompt = False
        elif configuration == '4':
            configuration_name = "E3C4 - RegularResponse (no prompt)"
            bot_response = f"{regular_response}."
            needs_prompt = False
        elif configuration == '6':
            configuration_name = "E3C6 - RegularResponse (prompt)"
            bot_response = f"{regular_response}."
            needs_prompt = True
        elif configuration == '7':
            configuration_name = "E3C7 - Avoidance (Contextual) : {}".format(offense_type)
            bot_response = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['Avoidance']))
            needs_prompt = True
        elif configuration == '8':
            configuration_name = "E3C8 - PointingOut (Contextual) : {}".format(offense_type)
            bot_response = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['PointingOut']))
            needs_prompt = True
        elif configuration == '9':
            configuration_name = "E3C9 - Empathetic (Contextual) : {}".format(offense_type)
            bot_response = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
            needs_prompt = True
        # CONTEXTUAL STRATEGIES CROSSED
        elif len(username) > 0 and configuration == 'A':
            configuration_name = "E4CA - Empathetic (Contextual) + Username : {}".format(offense_type)
            contextual_response = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
            bot_response = f"{contextual_response[:-1]}, {username}{contextual_response[-1]}"
            needs_prompt = True
        elif len(username) > 0 and configuration == 'B':
            configuration_name = "E4CB - PointingOut (Contextual) + Username : {}".format(offense_type)
            contextual_response = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['PointingOut']))
            bot_response = f"{contextual_response[:-1]}, {username}{contextual_response[-1]}"
            needs_prompt = True
        elif len(username) > 0 and configuration == 'C':
            configuration_name = "E4CC - Empathetic (Contextual) + Username (no prompt): {}".format(offense_type)
            contextual_response = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
            bot_response = f"{contextual_response[:-1]}, {username}{contextual_response[-1]}"
            needs_prompt = True
        elif len(username) > 0 and configuration == 'D':
            configuration_name = "E4CD - PointingOut (Contextual) + Username (no prompt): {}".format(offense_type)
            contextual_response = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['PointingOut']))
            bot_response = f"{contextual_response[:-1]}, {username}{contextual_response[-1]}"
            needs_prompt = True
        elif configuration == 'E':
            configuration_name = "E4CE - Empathetic (Contextual) (no prompt): {}".format(offense_type)
            bot_response = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
            needs_prompt = True
        else:
            configuration_name = "E4CF - PointingOut (Contextual) (no prompt): {}".format(offense_type)
            bot_response = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['PointingOut']))
            needs_prompt = True
        # # WHY RESPONSE FOLLOW UP
        # elif len(username) > 0 and configuration == 'G':
        #     configuration_name = "E4CG - WhyResponse + Username (no prompt) - Empathetic Followup : {}".format(offense_type)
        #     followup = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
        #     bot_response = "{}, {}?".format(why_utterance, username)
        #     needs_prompt = False
        # elif configuration == 'H':
        #     configuration_name = "E4CH - WhyResponse (no prompt) - Empathetic Followup : {}".format(offense_type)
        #     followup = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['Empathetic']))
        #     bot_response = "{}?".format(why_utterance)
        #     needs_prompt = False
        # elif len(username) > 0 and configuration == 'I':
        #     configuration_name = "E4CI - WhyResponse + Username (no prompt) - Avoidance Followup : {}".format(offense_type)
        #     followup = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['Avoidance']))
        #     bot_response = "{}, {}?".format(why_utterance, username)
        #     needs_prompt = False
        # else:
        #     configuration_name = "E4CJ - WhyResponse (no prompt) - Avoidance Followup : {}".format(offense_type)
        #     followup = self.choose(tuple(CONTEXTUAL_RESPONSES[offense_type]['Avoidance']))
        #     bot_response = "{}?".format(why_utterance)
        #     needs_prompt = False

        # TODO this is a janky way of using state -- Caleb
        if followup:
            state.followup = followup
        if not needs_prompt:
            state.handle_response = True

        state.experiment_configuration = configuration_name
        logger.primary_info(f'Offensive User Experiment: {configuration_name}, bot_response: {bot_response}.') # type: ignore

        return bot_response, needs_prompt
