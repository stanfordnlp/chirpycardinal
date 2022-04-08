# This file is currently inactive, awaiting resurrection

# import logging
# from typing import Optional, Tuple
# from chirpy.response_generators.movies.treelets import abstract_treelet
# from chirpy.core.regex.regex_template import RegexTemplate
# from chirpy.core.regex.util import OPTIONAL_TEXT, NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, \
#     OPTIONAL_TEXT_MID
# from enum import Enum
# from chirpy.response_generators.food.regex_templates import FavoriteTypeTemplate
# from chirpy.core.response_generator_datatypes import PromptType, ResponseGeneratorResult
# from chirpy.core.response_priority import ResponsePriority, PromptType
# from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_EXPECTED_TYPE
# from chirpy.core.response_generator import Treelet
# import random
# from chirpy.response_generators.food.food_helpers import *
# from chirpy.response_generators.food.state import State, ConditionalState
#
# class GetOtherTypeTreelet(Treelet):
#     name = "get_other_type_treelet"
#
#     # Types of response that we might expect from the user
#     class UserResponses(Enum):
#         default = 1
#         random = 2
#         unknown_type = 3
#         recognized_type = 4
#         refused = 5
#
#     def __name__(self):
#         return "get_other_type"
#
#     def classify_user_response(self, state: State, utterance: str):
#         response = self.UserResponses.default
#         slots = {}
#         strong_response_flag = False
#
#         if state.repeat_count >= 2:
#             strong_response_flag = False
#             response = None
#             return response, slots, strong_response_flag
#
#         slots = FavoriteTypeTemplate().execute(utterance)
#         if slots is not None:
#             if is_known_food(slots['type']):
#                 response = self.UserResponses.recognized_type
#             else:
#                 response = self.UserResponses.unknown_type
#             strong_response_flag = True
#         else:
#             strong_response_flag = False
#             response = self.UserResponses.random
#
#         if self.is_no(utterance):
#             strong_response_flag = False
#             response = self.UserResponses.refused
#
#         return response, slots, strong_response_flag
#
#     def get_response(self, state):
#         """ Returns the response as a string. """
#         response, slots, strong_response_flag = self.classify_user_response(state, self.rg.state_manager.current_state.text)
#
#
#
#         if response == self.UserResponses.refused:
#             return ResponseGeneratorResult(text="Ok, sure.", priority=ResponsePriority.STRONG_CONTINUE,
#                                            needs_prompt=True, state=state,
#                                            cur_entity=entity,
#                                            conditional_state=ConditionalState())
#         elif response == self.UserResponses.random:
#             return ResponseGeneratorResult(text="Hmm, I haven't heard of that.", priority=ResponsePriority.WEAK_CONTINUE,
#                                            needs_prompt=True, state=state,
#                                            cur_entity=entity,
#                                            conditional_state=ConditionalState())
#         elif response == self.UserResponses.unknown_type:
#             unknown_type_responses = ["Oh, I haven't heard of that.", "Cool, I haven't tried that before.",
#                                     "Interesting, I've never had that."]
#             response_text = random.choice(unknown_type_responses) + " "
#             # Choose known type
#             food_class = entity.name
#             known_type = list(get_types_of(food_class))[0] # May not want this to be random for consistency
#             food_containing_type = list(get_foods_containing(known_type))[0]
#             containing_food_class = food_containing_type if len(get_types_of(food_containing_type)) != 0 else get_class_of(food_containing_type)
#             mention_known_type_responses = [f"Personally, I enjoy {known_type}, especially in a {food_containing_type}.",
#                                             f"One of my favorite kinds of {food_class} is {known_type}, particularly in a {food_containing_type}."]
#             response_text += random.choice(mention_known_type_responses)
#             return ResponseGeneratorResult(text=response_text, priority=ResponsePriority.FORCE_START,
#                                            needs_prompt=False, state=state,
#                                            cur_entity=entity,
#                                            conditional_state=ConditionalState(cur_treelet_str='get_favorite_type',
#                                                                               cur_food=containing_food_class,
#                                                                               prev_foods=prev_foods))
#         else:
#             food_class = entity.name
#             known_type = list(get_types_of(food_class))[0] # May not want this to be random for consistency
#             food_containing_type = list(get_foods_containing(slots['type']))[0]
#             containing_food_class = food_containing_type if len(get_types_of(food_containing_type)) != 0 else get_class_of(food_containing_type)
#             response = f"Oh yeah, I love {slots['type']} too. I especially like it in a {food_containing_type}."
#             prev_foods = state.prev_foods
#             prev_foods.extend([slots['type'], known_type])
#             return ResponseGeneratorResult(text=response, priority=ResponsePriority.FORCE_START,
#                                            needs_prompt=False, state=state,
#                                            cur_entity=entity,
#                                            conditional_state=ConditionalState(cur_treelet_str='get_favorite_type',
#                                                                               cur_food=containing_food_class,
#                                                                               prev_foods=prev_foods))
#
#     def get_prompt(self) -> (str, PromptType):
#         """ Returns the prompt that should be used if this treelet is currently active"""
#         pass
