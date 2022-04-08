"""
    Trenton Chang, Caleb Chiam - Nov. 2020
    personal_issues_response_generator.py

    The following response generator is intended to provide the user with an emotionally supportive experience, and converse
    meaningfully with users about their emotional experiences. This RG is NOT intended to offer any professional mental health or
    psychological advice.

    In general, this RG utilizes a mix of ELIZA-like behaviors like paraphrasing/open-ended questioning AND modular validation/questioning
    turn construction to simulate active listening skills in human communication.

"""

import logging
from datetime import datetime

from chirpy.annotators.corenlp import Sentiment

from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import emptyResult_with_conditional_state, ResponseGeneratorResult, \
    PromptResult, emptyPrompt, UpdateEntity

from chirpy.response_generators.personal_issues.state import State, ConditionalState
from chirpy.response_generators.personal_issues.treelets import *
from chirpy.response_generators.personal_issues.personal_issues_helpers import *
from chirpy.response_generators.personal_issues.personal_issues_helpers import ResponseType
from chirpy.response_generators.personal_issues.response_templates.response_components import *

logger = logging.getLogger('chirpylogger')


class PersonalIssuesResponseGenerator(ResponseGenerator):
    name='PERSONAL_ISSUES'
    def __init__(self, state_manager) -> None:
        name = 'PERSONAL_ISSUES'

        self.first_turn_treelet = FirstTurnTreelet(self)
        self.subsequent_turn_treelet = SubsequentTurnTreelet(self)
        self.possible_continue_treelet = PossibleContinueTreelet(self)
        self.possible_continue_accepted_treelet = PossibleContinueAcceptedTreelet(self)
        self.ending_treelet = EndingTreelet(self)

        self.treelets = {
            treelet.name: treelet for treelet in [self.first_turn_treelet,
                                                  self.subsequent_turn_treelet,
                                                  self.possible_continue_treelet,
                                                  self.possible_continue_accepted_treelet,
                                                  self.ending_treelet]
        }

        disallow_start_from = [
            'OPINION', 'WIKI', 'ALIENS', 'MUSIC', 'CATEGORIES'
        ]

        super().__init__(state_manager,
                         treelets=self.treelets,
                         transition_matrix=self.init_transition_matrix(),
                         disallow_start_from=disallow_start_from,
                         can_give_prompts=False,
                         state_constructor=State,
                         conditional_state_constructor=ConditionalState
                         )

    def init_transition_matrix(self):
        transition_matrix = {
            self.first_turn_treelet.name: {
                ResponseType.NO: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.DISINTERESTED: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.IS_CONTINUED_SHARING: (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.PERSONAL_SHARING_NEGATIVE: (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.SHORT_RESPONSE: (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.GRATITUDE: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE)
            },
            self.subsequent_turn_treelet.name: {
                ResponseType.DISINTERESTED: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.PERSONAL_SHARING_NEGATIVE: (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.IS_CONTINUED_SHARING: (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: state.question_last_turn and ResponseType.SHORT_RESPONSE in response_types:
                    (self.possible_continue_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: state.question_last_turn and
                                              (ResponseType.YES in response_types or ResponseType.NO in response_types):
                    (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: not state.question_last_turn and
                                              (ResponseType.GRATITUDE in response_types or ResponseType.NO in response_types):
                    (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: not state.question_last_turn and ResponseType.SHORT_RESPONSE in response_types:
                    (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: not state.question_last_turn and ResponseType.YES in response_types:
                    (self.possible_continue_accepted_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: True: (self.possible_continue_treelet, ResponsePriority.WEAK_CONTINUE)
            },
            self.possible_continue_treelet.name: {
                ResponseType.NO: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.GRATITUDE: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.DISINTERESTED: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.YES: (self.possible_continue_accepted_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.PERSONAL_SHARING_NEGATIVE: (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.IS_CONTINUED_SHARING: (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.SHORT_RESPONSE: (self.ending_treelet, ResponsePriority.WEAK_CONTINUE),
                ResponseType.NONCOMMITTAL: (self.ending_treelet, ResponsePriority.WEAK_CONTINUE)
            },
            self.possible_continue_accepted_treelet.name: {
                ResponseType.PERSONAL_SHARING_NEGATIVE: (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.IS_CONTINUED_SHARING: (self.subsequent_turn_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.GRATITUDE: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.DISINTERESTED: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.NO: (self.ending_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.YES: (self.possible_continue_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.NONCOMMITTAL: (self.possible_continue_treelet, ResponsePriority.STRONG_CONTINUE)
            },
            self.ending_treelet.name: {} # NO-OP

        }
        return transition_matrix

    def get_intro_treelet_response(self):
        # don't allow PI to trigger soon after last trigger
        if datetime.now() >= datetime(2021, 7, 1):
            if self.get_current_state().turns_since_last_active[self.name] < 15:
                return self.emptyResult()
            if ResponseType.PERSONAL_SHARING_NEGATIVE in self.response_types:
                return self.first_turn_treelet.get_response(ResponsePriority.FORCE_START)
        else:
            return self.emptyResult()

    def identify_response_types(self, utterance):
        response_types = super().identify_response_types(utterance)

        if is_gratitude_response(self, utterance):
            response_types.add(ResponseType.GRATITUDE)

        if is_personal_issue(self, utterance):

            response_types.add(ResponseType.PERSONAL_SHARING_NEGATIVE)

        if is_continued_sharing(self, utterance):
            response_types.add(ResponseType.IS_CONTINUED_SHARING)

        if is_noncommittal_response(self, utterance):
            response_types.add(ResponseType.NONCOMMITTAL)

        if is_short_response(utterance):
            response_types.add(ResponseType.SHORT_RESPONSE)
        #
        # if len(response_types) == 0:
        #     response_types.add(ResponseType.UNKNOWN_TYPE)

        return response_types
