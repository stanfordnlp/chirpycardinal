import logging

from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from typing import Optional, List
import itertools
logger = logging.getLogger('chirpylogger')


class NeuralGraphemeToPhoneme(Annotator):
    name='g2p'
    def __init__(self, state_manager: StateManager, timeout=1, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data:str) -> List[str]:
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return None

    def execute(self, input_data: Optional[str]=None) -> List[str]:
        """
        Run emotion classifier on input_data and return an emotion label.
        The emotion classifier is trained on Empathetic Dialogues Dataset (https://arxiv.org/abs/1811.00207)
        to predict the emotion given an utterance

        Args:
            input_data (str): text to be segmented into sentences
                "utterance": Input to emotion classifier

        Returns:
            List[str]: List of strings, each a sentence from the text
        """
        if input_data is None:
            return []


        logger.debug(f'Calling g2p Remote module with text="{input_data}"')
        output = self.remote_call({'text': input_data})
        if not output or output.get('error', False):
            logger.error(f'Error when running SentSeg Remote Module. \n'
                         f'Response: {output}.')
            return self.get_default_response(input_data)
        else:
            if 'response' in output:
                return output['response']
            else:
                return self.get_default_response(input_data)

