import logging

from typing import List, Optional
from dataclasses import dataclass

from chirpy.core import flags
from chirpy.core.callables import Annotator
from chirpy.core.experiment import EXPERIMENT_NOT_FOUND
from chirpy.core.latency import measure
from chirpy.core.state_manager import StateManager
from chirpy.core.util import filter_and_log, contains_phrase

logger = logging.getLogger('chirpylogger')

CONVPARA_CONFIG = {
     'no_sample': False,
     'max_length': 50,
     'min_length': 5,
     'temperature': 0.9,
     'top_k': 0,
     'top_p': 0.85,
     'num_samples': 3,
     'seed': 4230
}

HISTORY_UTTERANCES = 2
@dataclass
class ConvParaphrase:
    text: str
    prob: float
    finished: bool
    tokens: List[str]
    token_probabilities: List[float]


    def readable_text(self):
        text = self.text.replace('LOL', '')
        return text


class ConvPara(Annotator):
    name='convpara'
    def __init__(self, state_manager: StateManager, timeout=2):
        super().__init__(state_manager=state_manager, timeout=timeout)

    def get_default_response(self, input_data=None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return []

    @measure
    def get_paraphrases(self, background: str, entity: str, config: dict = {}):
        """
        Args:
            background: The background information that is to be conversationally paraphrased
            entity: the entity to be paraphrased

        Returns:
            paraphrases: List[str]
        """
        convpara_experiment = self.state_manager.current_state.experiments.look_up_experiment_value('convpara')
        if convpara_experiment == False:
            return self.get_default_response()
        history = self.state_manager.current_state.history
        user_utterance = self.state_manager.current_state.text
        if len(history)>=1:
            history = history[-1:] + [user_utterance]
        else:
            logger.warning("ConvPara called with fewer than 2 history turns")
            return self.get_default_response()
        input_data = {
            'background': background,
            'history': history,
            'entity': entity,
            'config': {}
        }
        top_p = self.state_manager.current_state.experiments.look_up_experiment_value('convpara_top_p')
        if top_p == EXPERIMENT_NOT_FOUND:
            CONVPARA_CONFIG['top_p'] = top_p

        CONVPARA_CONFIG['seed'] = hash(self.state_manager.current_state.session_id)

        # Add default config parameters if they were not supplied
        for k, v in CONVPARA_CONFIG.items():
            input_data['config'][k] = config.get(k, v)

        return_dict = self.remote_call(input_data)
        if not return_dict:
            return return_dict

        paraphrases = [ConvParaphrase(t, p, f, tt, tp) for t, p, f, tt, tp in zip(return_dict['paraphrases'], return_dict['probabilities'],
        return_dict['paraphrase_ended'], return_dict['paraphrase_tokens'], return_dict['paraphrase_token_probabilities'])]
        logger.primary_info(f"For text {background}, received paraphrases {paraphrases}")

        paraphrases = list(filter(lambda paraphrase: not contains_phrase(paraphrase.text, {'bye', 'goodbye', 'nice chatting'}), paraphrases))
        #paraphrases.sort(key=lambda paraphrase: paraphrase.prob, reverse=True)
        #Fixme: heuristic checks go here
        return paraphrases


