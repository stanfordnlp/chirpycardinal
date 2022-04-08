import json
import logging

from typing import List, Dict, Optional  # NOQA

from chirpy.core import flags
from chirpy.core.callables import Annotator, get_url
from chirpy.core.state_manager import StateManager
from chirpy.core.util import contains_phrase
from chirpy.core.regex.templates import CurrentEventsTemplate

logger = logging.getLogger('chirpylogger')

#For reference
QUESTION_THRESHOLD = 0.60


class QuestionAnnotator(Annotator):
    name='question'
    def __init__(self, state_manager: StateManager, timeout=1.5, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)


    def get_default_response(self, input_data: Optional[Dict] = None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return {"is_question": False, "question_prob": 0}

    def execute(self, input_data: Optional[Dict] = None):
        """
        Run question classifier trained on modified MIDAS dataset (https://arxiv.org/abs/1908.10023)

        Args:
            input_data (Dict): Dict with key "utterance": Current utterance. This is the utterance that is classified

        Returns:
            If input_data is not None:
                Dict: A dict with key is_question, whether the utterance is predicted as a question
                and question_prob, the probability that the utterace is a question

            If input_data is None:
                Dict: A dict with is_question and question_prob
        """
        user_utterance = self.state_manager.current_state.text
        if input_data is None:
            input_data = {'utterance': user_utterance}

        if not input_data['utterance']:
            return self.get_default_response()

        if CurrentEventsTemplate().execute(input_data['utterance']):
            question_prob = 0.
            is_question = False
            logger.primary_info("Detected Current Events intent, setting is_question=False and question_prob=0")
            return {"question_prob": question_prob, "is_question": is_question}

        # NOTE: Errors thrown (including ones for timeouts) are not caught here. They should be caught by the caller.
        # Don't return default response here. That will be handled by save_and_execute.
        # Just catch new errors and throw them, or return the result
        # All the error logging should happen here
        logger.primary_info(f'Calling Question Classifier Remote module with data="{input_data}"')

        output = super().remote_call(input_data)
        logger.primary_info(f"Question Classifier Remote module returned output: {output}")

        if output is None:
            default_response = self.get_default_response()
            logger.warning(f'{type(self).__name__} using default response: {default_response}')
            return default_response

        try:
            question_prob = output['response'][0]
            is_question = (question_prob >= QUESTION_THRESHOLD)
        except KeyError:
            default_response = self.get_default_response()
            logger.warning(f'{type(self).__name__} using default response: {default_response}')
            return default_response



        output_dict = {"question_prob": question_prob, "is_question": is_question}

        logger.primary_info(f'Question classifier predicts probability that utterance is question "{question_prob}')
        return output_dict


if __name__ == "__main__":
    # You can test the dialog classifier below
    import requests
    import json
    class TestModule:
        def __init__(self, url):
            self.url = url
        def execute(self, data):
            response = requests.post(self.url, data=json.dumps(data), headers={'content-type': 'application/json'}, timeout=10)
            return response
    url = get_url("question")
    module = TestModule(url)
    output = module.execute({"utterance": "my day was good how about you"}).json()
    print(output)
