import logging

from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from chirpy.core.latency import measure

logger = logging.getLogger('chirpylogger')

class ResponseRanker(Annotator):
    name='responseranker'
    def __init__(self, state_manager: StateManager, timeout=3, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data=None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        N = len(input_data['responses'])
        return {"error": True, "score": [0] * N, "updown": [0] * N}

    @measure
    def execute(self, input_data=None):
        """
            Input data should be a dict with keys 'context', 'responses', where
            - 'context': User's last utterance, type str.
            - 'responses': Possible next-turn responses, type List[str].
            - 'config': Remote module configuration; currently, just a dict mapping to bools to determine which ranking models to use.

            It returns a mapping of possible responses to 'updown', 'width', and 'depth' scores as
            given by the DialogRPT (https://arxiv.org/abs/2009.06978) model family in the SAME ORDER as
            those passed in by responses:
            - 'updown': List[float] in [0, 1]
            - 'width': List[float] in [0, 1]
            - 'depth': List[float] in [0, 1]

            Higher is better. Each model call can be expected to take 20-30ms per sequence.
        """
        results = self.remote_call(input_data)
        return results
