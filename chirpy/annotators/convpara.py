import logging

from typing import List, Optional
from dataclasses import dataclass
from functools import lru_cache

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
     'temperature': 0.7,
     'top_k': 0,
     'top_p': 0.7,
     'num_samples': 8,
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
    token_probabilities_no_history: List[float]
    token_probabilities_no_knowledge: List[float]
    token_probabilities_no_history_no_knowledge: List[float]
    pmi_rank: Optional[int] = None
    pmi_h_rank: Optional[int] = None
    pcmi_h_rank: Optional[int] = None

    # (Top 75% by pcmi_h_rank & Top-50% by pmi-rank) +(Bottom 25% by pcmi_h_rank & Top-50% by pmi-rank)
    # + (Bottom 50% by pmi-rank)
    # This ranking is to be used if there's any subsequent filtering and one needs a ranked list
    # Otherwise top_fused_pcmi is probably better
    fused_pcmi_rank: Optional[int]= None

    # This uses the heuristic from the paper: if the top pmi is in the lower 25% of pcmi_h ranks, then pick an alternative
    # That is in the top 50% by pmi and top 25% by pcmi_h. This is different from how the fused_pcmi_rank is computed
    # which imposes an ordering over all the candidates.
    # If this value is set to True, this is the candidate that would have been chosen by the fused-pcmi strategy
    top_fused_pcmi: bool = False
    top_fused_pmi: bool = False

    lru_cache(maxsize=4)
    def log_prob(self, probs):
        return sum(map(math.log, probs))

    lru_cache(maxsize=1)
    @property
    def pmi(self):
        return self.log_prob(self.token_probabilities) - self.log_prob(self.token_probabilities_no_history_no_knowledge)

    lru_cache(maxsize=1)
    @property
    def pmi_h(self):
        return self.log_prob(self.token_probabilities_no_knowledge) - self.log_prob(self.token_probabilities_no_history_no_knowledge)

    lru_cache(maxsize=1)
    @property
    def pmi_k(self):
        return self.log_prob(self.token_probabilities_no_history) - self.log_prob(self.token_probabilities_no_history_no_knowledge)

    lru_cache(maxsize=1)
    @property
    def pcmi_h(self):
        return self.pmi - self.pmi_k

    lru_cache(maxsize=1)
    @property
    def pcmi_k(self):
        return self.pmi - self.pmi_h



    def readable_text(self):
        text = self.text.replace('LOL', '').replace(r' lol', ' ')
        return text

def select_fused_pcmi_h_candidate(paraphrases: List[ConvParaphrase]):
    for p in paraphrases: p.top_fused_pcmi = False
    pmi_sorted_paraphrases: List[ConvParaphrase] = sorted(paraphrases, key=lambda paraphrase: paraphrase.pmi,
                                                          reverse=True)
    pcmi_h_sorted_paraphrases: List[ConvParaphrase] = sorted(paraphrases, key=lambda paraphrase: paraphrase.pcmi_h,
                                                             reverse=True)
    n = len(paraphrases)
    for (rank, p) in zip(range(n), pcmi_h_sorted_paraphrases): p.pcmi_h_rank = rank
    for (rank, p) in zip(range(n), pmi_sorted_paraphrases): p.pmi_rank = rank
    selected_paraphrase = pmi_sorted_paraphrases[0]

    fused_pcmi_h_candidates = [p for p in pmi_sorted_paraphrases[:-(n // 2)] if p.pcmi_h_rank <= n // 4]
    if len(fused_pcmi_h_candidates) > 0 and selected_paraphrase.pcmi_h_rank >= (3 * n) // 4:
        selected_paraphrase = fused_pcmi_h_candidates[0]
    selected_paraphrase.top_fused_pcmi = True
    return selected_paraphrase

def select_fused_pmi_h_candidate(paraphrases: List[ConvParaphrase]):
    for p in paraphrases: p.top_fused_pmi = False
    pmi_sorted_paraphrases: List[ConvParaphrase] = sorted(paraphrases, key=lambda paraphrase: paraphrase.pmi,
                                                          reverse=True)
    pmi_h_sorted_paraphrases: List[ConvParaphrase] = sorted(paraphrases, key=lambda paraphrase: paraphrase.pmi_h,
                                                             reverse=True)
    n = len(paraphrases)
    for (rank, p) in zip(range(n), pmi_h_sorted_paraphrases): p.pmi_h_rank = rank
    for (rank, p) in zip(range(n), pmi_sorted_paraphrases): p.pmi_rank = rank
    selected_paraphrase = pmi_sorted_paraphrases[0]

    fused_pmi_h_candidates = [p for p in pmi_sorted_paraphrases[:-(n // 2)] if p.pmi_h_rank <= n // 4]
    if len(fused_pmi_h_candidates) > 0 and selected_paraphrase.pmi_h_rank >= (3 * n) // 4:
        selected_paraphrase = fused_pmi_h_candidates[0]
    selected_paraphrase.top_fused_pmi = True
    return selected_paraphrase


class ConvPara(Annotator):
    name='convpara'
    def __init__(self, state_manager: StateManager, timeout=3):
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
        #top_p = self.state_manager.current_state.experiments.look_up_experiment_value('convpara_top_p')
        #if top_p == EXPERIMENT_NOT_FOUND:
        #    CONVPARA_CONFIG['top_p'] = top_p

        CONVPARA_CONFIG['seed'] = hash(self.state_manager.current_state.session_id)

        # Add default config parameters if they were not supplied
        for k, v in CONVPARA_CONFIG.items():
            input_data['config'][k] = config.get(k, v)

        return_dict = self.remote_call(input_data)
        if not return_dict:
            return return_dict

        paraphrases = [ConvParaphrase(t, p, f, tt, tp, tpnh, tpnk, tpnhk) for t, p, f, tt, tp, tpnh, tpnk, tpnhk in zip(
            return_dict['paraphrases'], return_dict['probabilities'], return_dict['paraphrase_ended'],
            return_dict['paraphrase_tokens'], return_dict['paraphrase_token_probabilities'], return_dict['no_history'],
            return_dict['no_knowledge'], return_dict['no_history_no_knowledge'])]

        logger.primary_info(f"For text {background}, received paraphrases {paraphrases}")

        paraphrases: List[ConvParaphrase] = list(filter(lambda paraphrase: not contains_phrase(paraphrase.text, {'bye', 'goodbye', 'nice chatting'}), paraphrases))
        if paraphrases is None: paraphrases = []

        n = len(paraphrases)
        top_pmi_paraphrase = max(paraphrases, key=lambda p: p.pmi)
        top_pmi_paraphrase.top_pmi = True
        pmi_sorted_paraphrases: List[ConvParaphrase] = sorted(paraphrases, key=lambda paraphrase: paraphrase.pmi, reverse=True)
        pcmi_h_sorted_paraphrases: List[ConvParaphrase] = sorted(paraphrases, key=lambda paraphrase: paraphrase.pcmi_h, reverse=True)
        for (rank, p) in zip(range(n), pcmi_h_sorted_paraphrases): p.pcmi_h_rank = rank
        for (rank, p) in zip(range(n), pmi_sorted_paraphrases): p.pmi_rank = rank
        fused_pcmi_h_candidates = [p for p in pmi_sorted_paraphrases[:-(n // 2)] if p.pcmi_h_rank <= n // 4]
        if len(fused_pcmi_h_candidates)>0 and pmi_sorted_paraphrases[0].pcmi_h_rank >= (3*n)//4:
            fused_pcmi_h_candidates[0].top_fused_pcmi = True
        else:
            pmi_sorted_paraphrases[0].top_fused_pcmi = True
        # (Top 75% by pcmi_h_rank & Top-50% by pmi-rank) +(Bottom 25% by pcmi_h_rank & Top-50% by pmi-rank)
        # + (Bottom 50% by pmi-rank)
        fused_pcmi_sorted_paraphrases = \
            [p for p in pmi_sorted_paraphrases[:-(n//2)] if p.pcmi_h_rank < (3*n)//4] + \
            [p for p in pmi_sorted_paraphrases[:-(n // 2)] if p.pcmi_h_rank >= (3*n)//4] + \
            pmi_sorted_paraphrases[-(n//2):]
        for (rank, p) in zip(range(n), fused_pcmi_sorted_paraphrases): p.fused_pcmi_rank = rank

        logging.warning(f"Returning paraphrases: {fused_pcmi_sorted_paraphrases}")
        #Fixme: heuristic checks go here
        return fused_pcmi_sorted_paraphrases
