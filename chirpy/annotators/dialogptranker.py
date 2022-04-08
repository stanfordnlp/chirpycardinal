import json
import logging

from typing import Dict, Optional

from chirpy.core import flags
from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from chirpy.core.util import contains_phrase

logger = logging.getLogger('chirpylogger')

class DialoGPTRanker(Annotator):
    name='dialogptranker'
    def __init__(self, state_manager: StateManager, timeout=4, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data: Optional[Dict] = None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return {'scores': []}

    def execute(self, input_data: Optional[Dict] = None):
        """
        Score responses with pretrained DialoGPT model

        Args:
            input_data (Dict): Dict with key
            "utterance": String representing user utterance
            "responses": List of responses to score

        Returns:
            If input_data is not None:
                Dict: A dict with key
                "scores": List of scores corresponding to responses
            If input_data is None:
                Dict: A dict with key
                "scores": Empty list
        """
        if input_data is None:
            return self.get_default_response()

        if 'utterance' not in input_data or 'responses' not in input_data:
            logging.error(f"Missing utterance/responses; input_data={input_data}")
            return self.get_default_response()

        logger.primary_info(f'Calling DialoGPT scorer with data="{input_data}"')

        output = super().remote_call(input_data)
        logger.primary_info(f"DialoGPT scorer returned output: {output}")

        if output is None:
            default_response = self.get_default_response()
            logger.warning(f'{type(self).__name__} using default response: {default_response}')
            return default_response
        try:
            scores = output['scores']
        except KeyError:
            default_response = self.get_default_response()
            logger.warning(f'{type(self).__name__} using default response: {default_response}')
            return default_response

        output_dict = {"scores": scores}
        return output_dict


if __name__ == "__main__":
    # You can test the dialog classifier below
    import requests
    import json
    class TestModule:
        def __init__(self, url):
            self.url = url
        def execute(self, data):
            response = requests.post(self.url, data=json.dumps(data), headers={'content-type': 'application/json'}, timeout=60)
            return response
    module = TestModule("http://ec2-34-239-160-40.compute-1.amazonaws.com")
    output = module.execute({"utterance": 'i like adele she\'s such a great singer', "responses": ["Yeah, I love Adele too!", "Adele is one of my favorite singer"]}).json()
    print(output)
