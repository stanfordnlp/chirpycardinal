import json
import logging
import operator

from typing import Dict, Optional

from chirpy.core.callables import Annotator, get_url
from chirpy.core.state_manager import StateManager
from chirpy.core.util import contains_phrase

logger = logging.getLogger('chirpylogger')

MAX_HISTORY_SIZE = 2  # how many previous utterances to use. Includes both bot and user utterances. Doesn't include user's current utterance

#For reference
DIALOG_ACTS = {'statement', 'back-channeling', 'opinion', 'pos_answer', 'abandon', 'appreciation', 'yes_no_question',
               'closing', 'neg_answer', 'other_answers', 'opinion', 'command', 'hold', 'complaint',
               'open_question_factual', 'open_question_opinion', 'comment', 'nonsense', 'dev_command', 'correction',
               'opening', 'clarifying_question', 'uncertain', 'non_complaint', 'open_question_personal'}

YES_ANSWER_THRESHOLD = 0.70 # TODO: set good threshold
NO_ANSWER_THRESHOLD = 0.70 # TODO: set good threshold

YES = {"yes", "ok", "sure", "yeah", "of course", "by all means", "sure", "agree", "definitely", "correct"
        "certainly", "absolutely", "indeed", "right", "affirmative", "in the affirmative", "agreed", "roger",
        "aye aye", "yeah", "yep", "yup", "ya", "uh-huh", "okay", "OK", "okey-dokey", "okey-doke", "yea", "aye",
        "course", "true", "that would be great", "that would be good", "sound good", "sounds good", "sound great", "sounds great"}
NEGATE_YES = {"of course not", "absolutely not", "certainly not", "definitely not", "not correct", "not true", "i'm okay",
              "i'm good", "no okay", "that's okay", "it's okay"}
NO = {"no", "nope", "nah", "not really", "incorrect", "under no circumstances","by no means", "not at all",
        "negative", "never", "not on your life", "no way", "no way Jose", "nay", "don't think so", "disagree", "rather not"}

class DialogActAnnotator(Annotator):
    name='dialogact'
    def __init__(self, state_manager: StateManager, timeout=1.5, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data: Optional[Dict] = None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return {'probdist': dict(zip(DIALOG_ACTS, [0]*len(DIALOG_ACTS))),
                'top_1': None, 'is_yes_answer': False, 'is_no_answer': False, 'personal_issue_score': 0., 'top_2': None}

    def get_top_pred(self, pred_proba):
        """
        Args:
            pred_proba (Dict): Dict where keys are dialog acts and values are the predicted probabilities

        Returns:
            dialogact (String): the dialog act with the highest probability
        """
        return max(pred_proba.items(), key=operator.itemgetter(1))[0]

    def get_top_k_pred(self, pred_proba, k):
        return [x[0] for x in sorted(pred_proba.items(), key=operator.itemgetter(1), reverse=True)][:k]

    def is_yes(self, utterance, pred_proba):
        """
        Args:
            utterance (String): user's utterance
            pred_proba (Dict): Dict where keys are dialog acts and values are the predicted probabilities

        Returns:
            Bool: whether or not the utterance is a yes answer
        """

        # NOTE: we want something like "not correct" to be negative answer
        if contains_phrase(utterance, YES) and not contains_phrase(utterance, NEGATE_YES):
            return True
        else:
            return pred_proba['pos_answer'] >= YES_ANSWER_THRESHOLD

    def is_no(self, utterance, pred_proba):
        """
        Args:
            utterance (String): user's utterance
            pred_proba (Dict): Dict where keys are dialog acts and values are the predicted probabilities

        Returns:
            Bool: whether or not the utterance is a no answer
        """
        if contains_phrase(utterance, NO) or contains_phrase(utterance, NEGATE_YES):
            return True
        else:
            return pred_proba['neg_answer'] >= NO_ANSWER_THRESHOLD

    def execute(self, input_data: Optional[Dict] = None):
        """
        Run dialog act classifier trained on MIDAS dataset (https://arxiv.org/abs/1908.10023) to predict dialog act

        Args:
            input_data (Dict): Dict with key 'instances' and value list of utterances, each element a dict with keys
                "context": Previous utterance
                "utterance": Current utterance. This is the utterance that is classified
                By default, it'll send a the current utterance, as a single element, for classification

        Returns:
            If input_data is not None:
                List[Dict]: List of dicts with the probability distribution over dialog acts and top dialog act
            If input_data is None:
                Dict: A dict with the probability distribution over dialog acts and top dialog act
        """

        utterances = []

        if input_data is None:
            user_utterance = self.state_manager.current_state.text
            if not user_utterance:
                return self.get_default_response()
            history = self.state_manager.current_state.history
            data = {'instances': [{'context': history[-1] if len(history)>0 else '', 'utterance': user_utterance}]}
            utterances = [user_utterance]

        else:
            assert 'instances' in input_data
            assert all('context' in e and 'utterance' in e for e in input_data['instances'])
            data = input_data
            utterances = [e['utterance'] for e in input_data['instances']]

        # NOTE: Errors thrown (including ones for timeouts) are not caught here. They should be caught by the caller.
        # Don't return default response here. That will be handled by save_and_execute.
        # Just catch new errors and throw them, or return the result
        # All the error logging should happen here
        logger.primary_info(f'Calling Dialog Act Classifier Remote module with data="{data}"')

        output = self.remote_call(data)
        if output is None or 'response' not in output:
            default_response = self.get_default_response()
            logger.info(f'{type(self).__name__} using default response: {default_response}')
            return default_response
        logger.primary_info(f'Received Dialog Act Classifier remote module response="{output}"')
        pred_probas = output['response']
        # top label will be the key of the item with the max value
        top_ks = [self.get_top_k_pred(pred_proba, k=2) for pred_proba in pred_probas]
        top_1s = [x[0] for x in top_ks]
        top_2s = [x[1] for x in top_ks]
        is_yes_answers = [self.is_yes(u, p) for u, p in zip(utterances, pred_probas)]
        is_no_answers = [self.is_no(u, p) for u, p in zip(utterances, pred_probas)]
        dict_list = [{'probdist': pred_proba, 'top_1': top_1, 'top_2': top_2,
                        'is_yes_answer': is_yes_answer, 'is_no_answer': is_no_answer,
                      'personal_issue_score': 0.}
                        for pred_proba, top_1, top_2, is_yes_answer, is_no_answer \
                        in list(zip(pred_probas, top_1s, top_2s, is_yes_answers, is_no_answers))]

        logger.primary_info(f'Dialog acts top 1 predictions are "{top_1s}"')

        if input_data is None:
            # Since we know we only classified the current utterance, no point in returning a list
            return dict_list[0]
        else:
            return dict_list


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
    url = get_url("dialogact")
    module = TestModule(url)
    output = module.execute({'instances': [{"context": "do you want to talk about movies?", "utterance": "i don't"}]}).json()
    print(output)
