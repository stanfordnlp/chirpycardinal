import json
import logging

from typing import Dict, Optional

from chirpy.core import flags
from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager
from chirpy.core.util import contains_phrase

logger = logging.getLogger('chirpylogger')

#For reference
QUESTION_THRESHOLD = 0.60

class NeuralEntityLinker(Annotator):
    name='entitylinker'
    def __init__(self, state_manager: StateManager, timeout=1.5, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)


    def get_default_response(self, input_data: Optional[Dict] = None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return {"is_question": False, "question_prob": 0}

    def execute(self, context, spans):
        input_data = {'context': list(context), 'spans': [list(x) for x in spans]}
        # logger.primary_info(f"Calling neural entity linker with {input_data}.")
        output = super().remote_call(input_data)
        logger.primary_info(f'Neural entity linker returned: {output}')
        return output


if __name__ == "__main__":
    # You can test the entity linker below
    import requests
    import json
    class TestModule:
        def __init__(self, url):
            self.url = url
        def execute(self, data):
            response = requests.post(self.url, data=json.dumps(data), headers={'content-type': 'application/json'}, timeout=10)
            return response
    module = TestModule("http://cobot-LoadB-4W5PPC5CWWEX-1125293663.us-east-1.elb.amazonaws.com")
    output = module.execute({"utterance": "my day was good how about you"}).json()
    print(output)
