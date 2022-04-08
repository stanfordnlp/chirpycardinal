# import random
# import logging
# from typing import Optional, Tuple
# from chirpy.response_generators.movies.treelets import abstract_treelet
# from chirpy.core.regex.regex_template import RegexTemplate
# from chirpy.response_generators.food.regex_templates import DoubtfulTemplate
# from enum import Enum
# from chirpy.core.response_generator_datatypes import PromptType, ResponseGeneratorResult, PromptResult
# from chirpy.core.response_priority import ResponsePriority, PromptType
# from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
# from chirpy.response_generators.food.treelets.abstract_treelet import Treelet, State, ConditionalState
# from chirpy.response_generators.food.food_helpers import *
# from chirpy.core.response_generator.treelet import Treelet
# from chirpy.response_generators.food.state import State, ConditionalState
#
# logger = logging.getLogger('chirpylogger')
#
# class AcknowledgeUserCommentTreelet(Treelet):
#     def __name__(self):
#         return "acknowledge_user_comment"
#
#     def classify_user_response(self):
#         assert False, "This should never be called."
#
#     def is_low_initiative(self):
#         corenlp_output = self.rg.state_manager.current_state.corenlp
#         return ((len(self.rg.state_manager.current_state.text.split()) <= 5 and not corenlp_output['nouns'] and not corenlp_output['proper_nouns'])
#             or len(self.rg.state_manager.current_state.text.split()) <= 3)
#
#     def get_response(self, state):
#         """ Returns the response. """
#         state, utterance, response_types = self.get_state_utterance_response_types()
#         entity = self.rg.get_current_entity(initiated_this_turn=False)
#         cur_food = state.cur_food
#
#         # if question, sample an unconditional response; if statement, just agree
#         if ResponseType.QUESTION in response_types:
#             prefix = ''
#         elif len(utterance.split()) < 2:
#             prefix = ''
#         else:
#             prefix = 'i agree, that makes sense. '
#         proposed_neural_responses, _ = self.get_neural_generation(utterance, prefix=prefix)
#         conditions = [lambda response: 'i like' in response or 'i love' in response,
#                       lambda response: get_ingredients_in(cur_food) is not None and any(ingredient in response for ingredient in get_ingredients_in(cur_food)),
#                      ]
#         neural_response = self.sample_good_response(proposed_neural_responses, conditions=conditions)
#
#         # Can we continue the conversation with a factoid?
#         factoid = get_factoid(cur_food)
#         if factoid is not None and not self.is_low_initiative():
#             text = f"{neural_response} {factoid}"
#             return ResponseGeneratorResult(text=text, priority=ResponsePriority.STRONG_CONTINUE,
#                                            needs_prompt=False, state=state,
#                                            cur_entity=entity,
#                                            conditional_state=ConditionalState(cur_treelet_str='continue_factoid_discussion',
#                                                                               cur_food=entity.name,
#                                                                               factoid=factoid))
#         else:
#             conclusion = get_concluding_statement(cur_food)
#             text = f"{neural_response} {conclusion}"
#             return ResponseGeneratorResult(text=text, priority=ResponsePriority.STRONG_CONTINUE,
#                                            needs_prompt=True, state=state,
#                                            cur_entity=None,
#                                            conditional_state=ConditionalState(cur_treelet_str=None,
#                                                                               cur_food=None))
#
#     def get_prompt(self, state):
#         return None
