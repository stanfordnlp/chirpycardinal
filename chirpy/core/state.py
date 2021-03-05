import pytz
import os
from typing import *
import json
from datetime import datetime
from functools import singledispatch
import copy
from dataclasses import dataclass, asdict, field

from chirpy.core.entity_tracker.entity_tracker import EntityTrackerState
from chirpy.core.experiment import Experiments
from chirpy.core.flags import SIZE_THRESHOLD
from chirpy.core.util import print_dict_linebyline, get_ngrams
import jsonpickle
import random
import logging

logger = logging.getLogger('chirpylogger')

# Set jsonpickle to always order keys alphabetically.
# ============================ Reason why we do this: ============================
# We jsonpickle python objects into strings and write them to the dynamodb StateTable.
# The jsonpickle strings might contain pointers (e.g. {"py/id": 3}) to objects within themselves.
# The pointers are relative to the ordering in the jsonpickled string.
# When we transfer the data from dynamodb StateTable to postgres, we turn the jsonpickled strings back into
# dictionaries. So in many cases, postgres contains pointers like {"py/id": 3} rather than the objects themselves.
# By making the order fixed (alphabetical), we can resolve the pointers and recover the data from postgres.
# ================================================================================
jsonpickle.set_encoder_options('simplejson', sort_keys=True)
jsonpickle.set_encoder_options('json', sort_keys=True)

class State(object):

    def __init__(self, session_id: str, creation_date_time: str = None, user_id=None) -> None:
        """
        Initialize a State object with provided fields.
        :param session_id: session id
        :param creation_date_time: state creation timestamp, default to None
        """
        # self.user_id = user_id
        self.session_id = session_id
        if creation_date_time is not None:
            self.creation_date_time = creation_date_time
        else:
            self.creation_date_time = str(datetime.utcnow().isoformat())
        '''
        TODO: pipeline & commit_id should go to agent
        storing commit_id as env variable so that we don't have to interface w/git 
        '''
        # A dictionary of experiment name to value of experiment variable
        self.history = []
        self.entity_tracker = EntityTrackerState()
        self.entity_tracker.init_for_new_turn()
        self.turn_num = 0
        self.experiments = Experiments()

    def update_from_last_state(self, last_state):
        self.history = last_state.history + [last_state.text, last_state.response]
        self.entity_tracker = copy.copy(last_state.entity_tracker)
        self.entity_tracker.init_for_new_turn()
        self.experiments = last_state.experiments
        self.turn_num = last_state.turn_num + 1
        try:
            self.turns_since_last_active = last_state.turns_since_last_active
        except AttributeError:
            pass

    @property
    def active_rg(self):
        """
        Returns the active RG.

        Returns:
            If two different RGs supplied the response and prompt, return the prompting RG.
            If a single RG supplied both response and prompt, return that RG.
            If neither is set, return None
        """
        try:
            last_active_rg = self.selected_prompt_rg or self.selected_response_rg
        except AttributeError:
            try:
                last_active_rg = self.selected_response_rg
            except AttributeError:
                return None
        return last_active_rg

    def get_rg_state(self, rg_name: str):
        """
        Tries to get rg_name's RG state from current_state and return it.
        If unable to get it, logs an error message and returns None.
        """
        if not hasattr(self, 'response_generator_states'):
            logger.error(f"Tried to get RG state for {rg_name} but current_state doesn't have attribute 'response_generator_states'")
            return None
        rg_states = self.response_generator_states
        if rg_name not in rg_states:
            logger.error(f"Tried to get RG state for {rg_name}, but current_state.response_generator_states doesn't have a state for {rg_name}")
            return None
        return rg_states[rg_name]

    def serialize(self):
        logger.debug(f'Running jsonpickle version {jsonpickle.__version__}')
        logger.debug(f'jsonpickle backend names: {jsonpickle.backend.json._backend_names}')
        logger.debug(f'jsonpickle encoder options: {jsonpickle.backend.json._encoder_options}')
        logger.debug(f'jsonpickle fallthrough: {jsonpickle.backend.json._fallthrough}')

        encoded_dict = {k: jsonpickle.encode(v) for k, v in self.__dict__.items()}
        total_size = sum(len(k) + len(v) for k, v in encoded_dict.items())
        if total_size > SIZE_THRESHOLD:
            logger.primary_info(
                f"Total encoded size of state is {total_size}, which is greater than allowed {SIZE_THRESHOLD}. \n"
                f"Size of each value in the dictionary is:\n{print_dict_linebyline({k: len(v) for k, v in encoded_dict.items()})}. \n")

            # Tries to reduce size of the current state
            self.reduce_size()
            encoded_dict = {k: jsonpickle.encode(v) for k, v in self.__dict__.items()}
            total_size = sum(len(k) + len(v) for k, v in encoded_dict.items())
        logger.primary_info(
            f"Total encoded size of state is {total_size}\n"
            f"Size of each value in the dictionary is:\n{print_dict_linebyline({k: len(v) for k, v in encoded_dict.items()})}. \n")
        return encoded_dict

    @classmethod
    def deserialize(cls, mapping: dict):
        decoded_items = {}
        logger.info(mapping.items())
        for k, v in mapping.items():
            try:
                decoded_items[k] = jsonpickle.decode(v)
            except:
                logger.error(f"Unable to decode {k}:{v} from past state")

        constructor_args = ['session_id', 'creation_date_time']
        base_self = cls(**{k: decoded_items[k] for k in constructor_args})
        
        for k in decoded_items:
            #if k not in constructor_args:
            setattr(base_self, k, decoded_items[k])
        return base_self

    def reduce_size(self):
        """
        Attribute specific size reduction
        """
        purgable_attributes = ['entity_linker', 'entity_tracker', 'response_results', 'prompt_results']
        objs = []

        logger.primary_info("Running reduce_size on the state object")
        # Collect all purgable objects from within lists and dicts
        for attr in purgable_attributes:
            try:
                attr = getattr(self, attr)
                if isinstance(attr, list):
                    objs += attr
                if isinstance(attr, dict):
                    objs += list(attr.values())
                else:
                    objs.append(attr)

            except AttributeError:
                logger.warning(f"State doesn't have purgable attribute {attr}")

        for obj in objs:
            if hasattr(obj, 'reduce_size'):
                # The max_size is supposed to be per item, but it is hard to set it from here
                # because of interactions with other items. So setting an arbitrary size of
                # SIZE_THRESHOLD/8
                old_size = len(jsonpickle.encode(obj))
                obj.reduce_size(SIZE_THRESHOLD/8)
                logger.primary_info(f"object: {obj}'s encoded size reduced using reduce_size() from {old_size} to {len(jsonpickle.encode(obj))}")
            else:
                logger.warning(f'There is no reduce_size() fn for object={obj}')

        # The reduce_size function is supposed to be in place, and hence we don't need to
        # set to explicitly put the purged objects back into lists and dicts

    def rank_by_overlap(self, choices: List[str], n_gram_size=2, n_past_bot_utterances=10) -> List[Tuple[str, float]]:

        """
        Rank given choices by n-gram overlap with n_past_bot_utterances
        This is a drop in replacement for random.shuffle except that it doesn't do it in place (shuffle does)
        Args:
            choices: List of choices to rank
            n_gram_size: length of n-grams to compute overlap with. 2 is a good number
            history_length: Number of past bot utterances to use, 10 seems like a good default

        Returns:
            Ranked list of the choices, ranked by increasing overlap

        """

        bot_utterances_to_consider = self.history[::-2][:n_past_bot_utterances]
        if len(bot_utterances_to_consider) == 0:
            return choices
        # NB: If the utterance has only 1 token, then get_ngrams doesn't return anything, hence the if condition
        bot_utterance_ngrams = [set(get_ngrams(r.lower(), n_gram_size)) if set(get_ngrams(r.lower(), n_gram_size)) else {r.lower()} for r in bot_utterances_to_consider]
        choices_ngrams = [set(get_ngrams(c.lower(), n_gram_size)) if set(get_ngrams(c.lower(), n_gram_size)) else {c.lower()} for c in choices]
        choice_overlap = [max(len(cn & bn)/len(cn) for bn in bot_utterance_ngrams) for cn in choices_ngrams]
        sorted_choices = sorted(zip(choices, choice_overlap), key=lambda tup: tup[1])
        logger.info(f"Choices sorted by {n_gram_size}-gram overlap with past {n_past_bot_utterances} bot utterances\n"+
                    '\n'.join(f"{overlap:.2f}\t{choice}" for choice, overlap in sorted_choices))
        return sorted_choices

    def choose_least_repetitive(self, choices: List[str], n_gram_size=2, n_past_bot_utterances=10)-> str:
        """Wrapper around rank_by_overlap
        This is a drop in replacement for random.choice
        """
        try:
            if len(choices) == 0:
                raise IndexError("Cannot choose from an empty sequence")
            sorted_choices = self.rank_by_overlap(choices, n_gram_size, n_past_bot_utterances)
            sorted_choice_strings = [choice for choice, overlap in sorted_choices]
            weights = [1-overlap for choice, overlap in sorted_choices]
            chosen_string = random.choices(sorted_choice_strings, weights=weights, k=1)[0]
            logger.info(f"Chose {chosen_string} based on a weighted sample of choices")
            return chosen_string
        except:
            return random.choice(choices)

    def __str__(self):
        """
        Override the default string behavior
        :return: string representation
        """
        return str(self.serialize())

    def __repr__(self):
        """
        Override the default string behavior
        :return: string representation
        """
        return self.__str__()
