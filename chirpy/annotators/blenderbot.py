import logging
from concurrent import futures
from collections import OrderedDict
from typing import List, Optional
import random
import json

from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from chirpy.core.latency import measure

CACHE = OrderedDict()
MAX_CACHE_SIZE = 1024

logger = logging.getLogger('chirpylogger')

NEURAL_DECODE_CONFIG = {
    'temperature': 0.7,
    'top_k': 5,
    'top_p': 0.9,
}

MAX_HISTORY_UTTERANCES = 3

def add_sentence_end_token(response):
    if response.strip()[-1] not in ['.', '!', '?']:
        response += '.'
    return response

class BlenderBot(Annotator):
    name='blenderbot'
    def __init__(self, state_manager: StateManager, timeout=3, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data=None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        # return [], []
        return {"responses": [], "response_probabilities": []}

    def get_history(self) -> List[str]:
        """
        Get the history of the conversation so far.
        Returns an odd-length list of strings, starting and ending with user utterances.
        """
        utterance_history = self.state_manager.current_state.history[-MAX_HISTORY_UTTERANCES - 1:]
        assert len(utterance_history) % 2 == 0, "utterance_history should be even length"
        user_utterance = self.state_manager.current_state.text
        return utterance_history + [user_utterance]

    def question_part(self, response) -> Optional[str]:
        """Returns the question part of the utterance, if there is one. Otherwise returns None"""
        if '?' not in response:
            return None
        question_idx = response.index('?')
        response = response[:question_idx].strip()
        other_punc_indices = [i for i in range(len(response)) if response[i] in ['.', ',', '!']]
        if not other_punc_indices:
            return response
        last_other_punc_index = max(other_punc_indices)
        response = response[last_other_punc_index+1:].strip()
        return response

    def edit_history_for_remote(self, history: List[str]) -> List[str]:
        """
        Returns the history as it should be given as input to the remote neural module

        Inputs:
            history: odd-length list of strings, starting and ending with user utterances, as it exists in the
                neuralchat state.

        Returns:
            new_history: odd-length list of strings, starting and ending with user utterances, as it should be fed to remote module
        """
        assert len(history) % 2 == 1

        new_history = [r for r in history]

        # Special case for handling start-of-conversation null turn. Here, we only use the part
        # of the starter question which is the actual question (if there is an actual question)
        if history[0] == '' and len(history) >= 2:
            question_part_only = self.question_part(history[1])
            if question_part_only:
                new_history[1] = question_part_only

        return new_history

    @measure
    def execute(self, input_data=None, prefix=None):
        """
        Generate responses from BlenderBot distilled.

        Args:
            input_data None, or dict with keys:
                "history": odd-length list of strings; the utterances to use as input to the model. History must be
                    odd-length, such that the first utterance is the user's. This is because the model was trained
                    on the EmpatheticDialogues dataset, which is asymmetric and always has the "user" go first.
                "config": dict. Contains settings for decoding. See GPT2ED_DECODE_CONFIG for format.

        Returns:
            responses: list of strings. The generated responses, with sentence-end tokens ('.') added if necessary.
        """
        if input_data is None:
            user_utterance = self.state_manager.current_state.text
            if hasattr(self.state_manager.current_state, 'dialogact') and self.state_manager.current_state.dialogact:
                if self.state_manager.current_state.question['is_question']:
                    user_utterance +='?'
            else:
                logger.debug("Did not append ? because dialogact was unavailable")
            history = self.edit_history_for_remote(self.get_history())
            curr_config = NEURAL_DECODE_CONFIG.copy()
            curr_config['min_length'] = random.randint(1, 5) * 5 # min length is 5, 10, 15, 20, or 25. Will usually result in utterances 0-3 tokens above min_length.
            input_data = {'history': history, 'config': curr_config}
        else:
            # Do some basic typechecks
            assert 'history' in input_data
            if 'config' not in input_data:
                input_data['config'] = NEURAL_DECODE_CONFIG

        if len(input_data['history']) == 1 and input_data['history'][0] == '':
            return [], []

        if prefix:
            input_data['prefix'] = prefix

        logger.primary_info(f'Sending this to BlenderBot remote module: {json.dumps(input_data)}')

        if hasattr(self.state_manager.current_state, 'blenderbot') and isinstance(self.state_manager.current_state.blenderbot, futures.Future):
            logger.primary_info("BlenderBot: Getting future result")
            future_result = self.state_manager.current_state.blenderbot.result()
            self.save_to_state(future_result)

        cache_key = str(input_data)
        if cache_key in CACHE:
            logger.primary_info("BlenderBot: Retrieving cached response")
            CACHE.move_to_end(cache_key)
            res = CACHE[cache_key]
        else:
            logger.primary_info("BlenderBot: Running remote call")
            res = self.remote_call(input_data)
            CACHE[cache_key] = res
            if len(CACHE) > MAX_CACHE_SIZE:
                CACHE.popitem(last=False)

        if res is None or len(res)==0:
            default_response = self.get_default_response()
            logger.info(f'{type(self).__name__} using default response: {default_response}')
            return default_response["responses"], default_response['response_probabilities']
        logger.primary_info(f'Received this from BlenderBot remote module: {res}')
        responses = [response.strip() for response in res['responses'] if response.strip()]  # list of strings
        responses = [add_sentence_end_token(response) for response in responses]  # add sentence end tokens if necessary
        return responses, res['response_probabilities']
