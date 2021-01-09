from typing import List

from chirpy.annotators.sentseg import NLTKSentenceSegmenter
from chirpy.core.response_generator_datatypes import emptyResult, ResponseGeneratorResult, emptyPrompt
import logging
from chirpy.core.util import contains_phrase, get_ngrams
from chirpy.core.callables import ResponseGenerator

logger = logging.getLogger('chirpylogger')

HANDOVER_TEXTS = ["Alright!", "Okay! Moving on.", "Sounds good!"]
CONVPARA_BLACKLISTED_ENTITIES = ['Black Lives Matter']

class Treelet():

    def __init__(self, rg: ResponseGenerator):
        super().__init__()
        self.rg = rg

    def __repr__(self):
        return "Treelet (WIKI)"



    def continue_response(self, base_response_result: ResponseGeneratorResult) -> ResponseGeneratorResult:
        raise NotImplementedError

    def handle_prompt(self, state) -> ResponseGeneratorResult:
        """
        Handle a prompt from previous turn

        Args:
            state: the rg state

        Returns:
            ResponseGeneratorResult: Should either respond with STRONG_CONTINUE, WEAK_CONTINUE, OR NONE

        Raises:
            CantRespondError if it is unable to respond
        """

        raise NotImplementedError

    def get_can_start_response(self, state):
        """
        Get's a response that starts discussion on an entity without any prompt from the previous turn

        Args:
            state: the rg state

        Returns:
            ResponseGeneratorResult: Should either respond with CAN_START OR NONE

        Raises:
            CantRespondError if it is unable to respond
        """
        return emptyResult(state)

    def get_prompt(self, state):
        return emptyPrompt(state)




    def ngram_recall(self, generations: List[str], original:str, n:int):
        original = original.lower()
        original_ngrams = set(get_ngrams(original, n))
        generated_ngrams = set(ngm for g in generations for ngm in get_ngrams(g, n))
        return len(generated_ngrams & original_ngrams)/len(original_ngrams)


    def get_sentseg_fn(self):
        def seg(text):
            return NLTKSentenceSegmenter(self.rg.state_manager).execute(text)

        return seg

    def is_yes(self, utterance : str) -> bool:
        """Quick helper method to return whether the user said yes

        :param utterance: user's utterance
        :type utterance: str
        :return: whether user said yes or not
        :rtype: bool
        """
        if self.rg.state_manager.current_state.dialog_act['is_yes_answer']:
            logger.primary_info('WIKI has dialog act predicting "is_yes_answer"')
            return True
        if contains_phrase(utterance, {'what else is interesting', 'what else'}):
            return True

        YES = {"yes", "ok", "sure", 'go on', 'yeah', 'okay', 'all', 'continue', 'yup', 'go ahead'}
        return contains_phrase(utterance, YES)

    def is_no(self, utterance : str) -> bool:
        """Quick helper method to return whether the user said no.
        We say that user said no if
        1. User said `no` or a variant of it
        2. User did not specify another entity to talk about

        :param utterance: user's utterance
        :type utterance: str
        :return: whether user said no or not
        :rtype: bool
        """
        if contains_phrase(utterance, {'what else is interesting', 'what else'}):
            return False
        if self.rg.state_manager.current_state.dialog_act['is_no_answer']:
            logger.primary_info('WIKI has dialog act predicting "is_no_answer"')
            return True

        NO = {"no", "don't", 'neither', 'else', 'nothing', 'nope', 'none', 'not', "don't care"}
        return contains_phrase(utterance, NO)


