import logging

from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from typing import Optional, List
import re
import itertools
logger = logging.getLogger('chirpylogger')


class NLTKSentenceSegmenter(Annotator):
    name='sentseg'
    def __init__(self, state_manager: StateManager, timeout=0.5, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data:str) -> List[str]:
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        try:
            return {'error': False, 'response': re.split('[.\n]', input_data)}
        except:
            return []

    def execute(self, input_data: Optional[str]=None) -> List[str]:
        """
        Run NLTK Sentence Segmenter on input_data and return a list of sentences.

        Args:
            input_data (str): text to be segmented into sentences

        Returns:
            List[str]: List of strings, each a sentence from the text
        """
        if input_data is None:
            return []


        logger.debug(f'Calling SentSeg Remote module with text="{input_data}"')
        #output = self.remote_call({'text': input_data})
        output = None
        if not output or output.get('error', False):
            logger.error(f'Error when running SentSeg Remote Module. \n'
                         f'Response: {output}.')
            return re.split('[.\n]', input_data)
            #raise RemoteServiceModuleError
        else:
            if 'response' in output:
                return [s.strip() for s in itertools.chain(*(s.split('\n') for s in output['response'])) if s.strip()]
            else:
                return self.get_default_response(input_data)
