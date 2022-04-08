import json
import logging

from typing import Dict, Optional

from chirpy.core import flags
from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from chirpy.core.util import contains_phrase
from chirpy.core.latency import measure

logger = logging.getLogger('chirpylogger')

#For reference
QUESTION_THRESHOLD = 0.60

class Infiller(Annotator):
    name='infiller'
    def __init__(self, state_manager: StateManager, timeout=4, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data: Optional[Dict] = None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return {'completions': [], 'error': True}

    @measure
    def execute(self, input_data: Optional[Dict] = None):
        """
        Uses pretrained BART to infill prompt templates

        Args:
            input_data (Dict): Dict with keys
                "contexts": Context for infilling prompts,
                "prompts": Prompt templates

        Returns:
            If input_data is None:
                Dict: A dict with key
                "completions": Empty list
            If input_data is not None:
                Dict: A dict with key
                "completions": List of completions, one completion per prompt
        """
        if input_data is None:
            return self.get_default_response()

        if ('contexts' not in input_data or 'prompts' not in input_data) and ('tuples' not in input_data or 'sentences' not in input_data):
            logging.error(f"Missing contexts/prompts; input_data={input_data}")
            return self.get_default_response()

        logger.primary_info(f'Calling BART contextual infilling module with data="{json.dumps(input_data)}"')

        output = super().remote_call(input_data)
        logger.primary_info(f"BART contextual infilling module returned output: {output}")

        if output is None:
            default_response = self.get_default_response()
            logger.warning(f'{type(self).__name__} using default response: {default_response}')
            return default_response
        try:
            completions = output['completions']
        except KeyError:
            default_response = self.get_default_response()
            logger.warning(f'{type(self).__name__} using default response: {default_response}')
            return default_response

        output_dict = output
        return output_dict


if __name__ == "__main__":
    # You can test the infiller below
    import requests
    import json
    class TestModule:
        def __init__(self, url):
            self.url = url
        def execute(self, data):
            response = requests.post(self.url, data=json.dumps(data), headers={'content-type': 'application/json'}, timeout=10)
            return response
    module = TestModule("http://ec2-3-214-217-42.compute-1.amazonaws.com")
    output = module.execute({"prompts": ["Yeah, I love [person] too!"], "contexts": ["i love chirpy"]}).json()
    print(output)
