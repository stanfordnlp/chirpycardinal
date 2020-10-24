import logging

from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from chirpy.core.latency import measure

logger = logging.getLogger('chirpylogger')

GPT2ED_DECODE_CONFIG = {
    'no_sample': False,
    'min_length': 4,  # in GPT2 tokens
    'max_length': 20,  # in GPT2 tokens
    'temperature': 0.7,
    'top_k': 0,
    'top_p': 0.9,
    'max_history_tokens': 800,  # in GPT2 tokens
    'num_samples': 20,
    'response_prefix': '',  # an optional prefix that all responses must start with
}

MAX_HISTORY_UTTERANCES = 3

def add_sentence_end_token(response):
    if response.strip()[-1] not in ['.', '!', '?']:
        response += '.'
    return response

class GPT2ED(Annotator):
    name='gpt2ed'
    def __init__(self, state_manager: StateManager, timeout=2, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data=None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return []
    
    @measure
    def execute(self, input_data=None):
        """
        Generate responses from GPT2 model trained on Empathetic Dialogues dataset (https://arxiv.org/abs/1811.00207)

        If input_data is provided, we pass the utterance as is and for a partial config, add rest of parameters as
        default from GPT2ED_DECODE_CONFIG.
        If input_data is None, we send the last MAX_HISTORY_UTTERANCES of the conversational history, using the settings
        in GPT2ED_DECODE_CONFIG.

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
            if hasattr(self.state_manager.current_state, 'dialog_act') and self.state_manager.current_state.dialog_act:
                if self.state_manager.current_state.question['is_question']:
                    user_utterance +='?'
            else:
                logger.debug("Did not append ? because dialog_act was unavailable")
            history = self.state_manager.current_state.history[-MAX_HISTORY_UTTERANCES - 1:]
            input_data = {'history': history+[user_utterance], 'config': GPT2ED_DECODE_CONFIG}
        else:
            # Do some basic typechecks
            assert 'history' in input_data
            if 'config' not in input_data:
                input_data['config'] = {}

            # Add default config parameters if they were not supplied
            for k, v in GPT2ED_DECODE_CONFIG.items():
                input_data['config'][k] = input_data['config'].get(k, v)
        logger.primary_info(f'Sending this to GPT2ED remote module: {input_data}')

        gpt2ed_response = self.remote_call(input_data)
        if gpt2ed_response is None or len(gpt2ed_response)==0:
            default_response = self.get_default_response()
            logger.info(f'{type(self).__name__} using default response: {default_response}')
            return default_response
        logger.primary_info(f'Received this from GPT2ED remote module: {gpt2ed_response}')
        responses = [response.strip() for response in gpt2ed_response['responses'] if response.strip()]  # list of strings
        responses = [add_sentence_end_token(response) for response in responses]  # add sentence end tokens if necessary

        # Following commented out code runs the dialog act classifier on the generated responses
        # But in the current implementation of the remote module takes 4 seconds, which is too long
        #context = input_data['history'][-1] if len(history) > 0 else ''
        #instances = [{'context': context, 'utterance': generation} for generation in responses]
        #dialog_acts = self.service_module_manager.get_module('dialog_act').execute(input_data = {'instances': instances})
        #responses = [{'response': response, 'dialog_act': da} for response, da in zip(responses, dialog_acts)]
        return responses

