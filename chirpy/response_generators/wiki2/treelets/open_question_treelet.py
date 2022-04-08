# from collections import Counter
# from copy import deepcopy
#
# import editdistance
# import logging
# import random
#
# from typing import Tuple, Optional, List
#
# import chirpy.core.offensive_classifier.offensive_classifier
# from chirpy.annotators.convpara import ConvPara
# from chirpy.annotators.gpt2ed import GPT2ED
# from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION
# from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
# from chirpy.core.latency import measure
# from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
# from chirpy.core.regex.templates import DontKnowTemplate, EverythingTemplate, NotThingTemplate, BackChannelingTemplate
# from chirpy.core.regex.response_lists import (
#     RESPONSE_TO_BACK_CHANNELING,
#     RESPONSE_TO_DONT_KNOW,
#     RESPONSE_TO_EVERYTHING_ANS,
#     RESPONSE_TO_NOTHING_ANS,
#     RESPONSE_TO_WHAT_ABOUT_YOU
# )
# from chirpy.response_generators.neural_fallback.neural_helpers import get_random_fallback_neural_response, neural_response_filtering
# from chirpy.response_generators.wiki2.state import State, ConditionalState
# from chirpy.core.response_generator.treelet import Treelet
# from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
# from chirpy.core.response_priority import ResponsePriority, PromptType
# from chirpy.core.util import filter_and_log
# from chirpy.response_generators.wiki2.treelets.open_questions import OPEN_QUESTIONS_DICTIONARY
# from chirpy.response_generators.wiki2.wiki_helpers import ResponseType
# from chirpy.response_generators.wiki2.wiki_utils import WikiSection, search_wiki_sections, clean_wiki_text, get_ngrams
#
# HANDOVER_TEXTS = ["Alright!", "Okay! Moving on.", "Sounds good!"]
#
# logger = logging.getLogger('chirpylogger')
#
# def ngram_recall(self, generations: List[str], original:str, n:int):
#     original = original.lower()
#     original_ngrams = set(get_ngrams(original, n))
#     generated_ngrams = set(ngm for g in generations for ngm in get_ngrams(g, n))
#     return len(generated_ngrams & original_ngrams)/len(original_ngrams)
#
#
# APOLOGY_TEXTS = ["Hmm, that does sound interesting. But I don\'t know much about that.",
#                  "Hmm, that is interesting. Unfortunately I don\'t know a lot about that."]
#
# # prompts to elicit open answers
# def open_answer_prompts(entity: WikiEntity, repeat=False):
#     prompts = [
#         f"What do you think about {entity.common_name}?",
#         f"On that note, do you have any thoughts on {entity.common_name}?",
#         f"What about {entity.common_name}, Do you have any thoughts on that?",
#     ]
#     return prompts
#
#
# def open_answer_prompts_after_user_rejection(entity, repeat=False):
#     acknowledge_rejection = [f"It sounds like you're not interested in the topics I suggested. I can tell you lots of other things about {entity}.",
#                              f"I'm hearing that you're not too excited about the topics I mentioned. No worries!",
#                              f"No worries! We can talk about different things regarding {entity}.",
#                              f"It sounds like you'd rather talk about a different aspect of {entity}.",
#                              f"That's ok! I can talk about other aspects of {entity} too!"]
#     prompts_after_user_rejected_subsection = [ f"What {'else ' if repeat else ''}about {entity} interests you?",
#                                                f"What {'other aspects ' if repeat else 'aspect '}of {entity} do you want to learn more about?",
#                                                f"What {'else ' if repeat else ''}would you like to know about {entity}?",
#                                                f"Which {'other ' if repeat else ''}aspects of {entity} would you like to talk about?"]
#     return " ".join([random.choice(acknowledge_rejection), random.choice(prompts_after_user_rejected_subsection)])
#
# class OpenQuestionTreelet(Treelet):
#     """In this treelet we ask open-ended questions to the user and respond with fuzzy matches to user's nounphrases """
#
#     name = "wiki_open_question_treelet"
#
#     @measure
#     def search_highlights(self, state) -> List[WikiSection]:
#         # else find overlap with section texts
#         utterance = self.rg.state_manager.current_state.text.lower()
#         entity = self.rg.get_recommended_entity(state)
#         noun_phrases = self.rg.state_manager.current_state.stanfordnlp['nounphrases']
#         linked_spans = [linked_span.span for linked_span in self.rg.state_manager.current_state.entity_linker.all_linkedspans]
#         linked_wikilinks = [e.name for linked_span in self.rg.state_manager.current_state.entity_linker.all_linkedspans for e in linked_span.ents_by_priority]
#         if not (noun_phrases or linked_spans):
#             search_sections = search_wiki_sections(entity.name, tuple([utterance]), tuple(linked_wikilinks))
#         else:
#             search_sections = search_wiki_sections(entity.name, tuple(noun_phrases+linked_spans), tuple(linked_wikilinks))
#         logger.debug(
#             f"Found following highlights in Wikipedia article for {entity.name} based on user utterance \n" + '\n'.join(
#                 [f"{s.title}, ({s.es_score}): {s.highlight}" for s in search_sections]))
#         # Remove sections that don't have any text
#         search_sections = filter(lambda s: s.highlight, search_sections)
#
#         # Remove sections that don't have a good overlap
#         search_sections = sorted(filter(lambda s: s.es_score > 5.5, search_sections), key=lambda s: s.es_score,
#                                  reverse=True)
#         return search_sections
#
#     def get_prompt_question(self, state, new_entity: Optional[WikiEntity] = None) -> Tuple[Optional[str], Optional[ConditionalState]]:
#         cur_entity = new_entity or self.rg.get_recommended_entity(state)
#
#         # This is just as a safety check to ensure we don't keep asking questions, because we probably won't do a good
#         # job for more than 2 turns anyways
#         if len(state.entity_state[cur_entity.name].highlights_used) >= 2:
#             logger.primary_info("Already gave open response twice, not prompting anymore")
#         if len(state.entity_state[cur_entity.name].neural_fallbacks_used) >= 2:
#             logger.primary_info("Already gave neural fallbacks twice, not prompting anymore")
#
#         # check if entity belongs to a valid entity group
#         for ent_group_name, ent_group in ENTITY_GROUPS_FOR_CLASSIFICATION.ordered_items:
#             if ent_group.matches(cur_entity) and ent_group_name in OPEN_QUESTIONS_DICTIONARY and \
#                     OPEN_QUESTIONS_DICTIONARY[ent_group_name]:
#                 break
#         else:
#             ent_group_name = None
#
#         if ent_group_name:
#             possible_open_question_types = set(OPEN_QUESTIONS_DICTIONARY[ent_group_name].keys())
#             entity_open_question_types_asked = set(state.entity_state[cur_entity.name].open_questions_asked)
#             all_open_questions_types_asked = set([q for ent in state.entity_state.values() for q in
#                                                   ent.open_questions_asked])
#             if len(possible_open_question_types - entity_open_question_types_asked) ==0:
#                 logger.primary_info(
#                     "Entity group identified, but questions for all returns types have been asked, not prompting anymore")
#             else:
#                 possible_open_question_types = possible_open_question_types - entity_open_question_types_asked
#                 never_asked_possible_open_question_types = possible_open_question_types - all_open_questions_types_asked
#
#                 # All types of open questions have been asked previously, so now just fall back to history weighted sampling
#                 if len(never_asked_possible_open_question_types) == 0:
#                     logger.info("All possible types of open questions have been asked, sampling using choose_least_repetitive")
#                     questions2rettype = {q: return_type for return_type, questions in OPEN_QUESTIONS_DICTIONARY[ent_group_name].items() for q in questions if return_type in possible_open_question_types}
#                     open_question = self.choose(list(questions2rettype.keys()))
#                     return_type = questions2rettype[open_question]
#                     logger.primary_info(
#                         f'WIKI has an open question {open_question} for {cur_entity} matching EntityGroup: "{ent_group_name}"')
#                     text = open_question.format(entity=cur_entity.common_name)
#                     conditional_state = ConditionalState(cur_doc_title=cur_entity.name,
#                                                          prev_treelet_str=self.name,
#                                                          open_question=(return_type, open_question))
#                 # Ask a question type which has never been asked
#                 else:
#                     for return_type, questions in OPEN_QUESTIONS_DICTIONARY[ent_group_name].items():
#                         if return_type in never_asked_possible_open_question_types and questions:
#                             open_question = self.choose(questions)
#                             logger.primary_info(
#                                 f'WIKI has an open question {open_question} for {cur_entity} matching EntityGroup: "{ent_group_name}"')
#                             text = open_question.format(entity=cur_entity.common_name)
#                             conditional_state = ConditionalState(cur_doc_title=cur_entity.name,
#                                                                  prev_treelet_str=self.name,
#                                                                  open_question=(return_type, open_question))
#                             break
#         else:
#             if len(state.entity_state[cur_entity.name].highlights_used) >= 1 or len(state.entity_state[cur_entity.name].neural_fallbacks_used) >= 1:
#                 logger.primary_info("Already asked a generic open question once, not prompting anymore")
#                 return None, None
#             if 'default' in state.entity_state[cur_entity.name].open_questions_asked:
#                 logger.primary_info("Already asked a generic open question once, not prompting anymore")
#                 return None, None
#             text = self.choose(open_answer_prompts(cur_entity,
#                                                    repeat=len(state.entity_state[cur_entity.name].highlights_used) > 0))
#             conditional_state = ConditionalState(cur_doc_title=cur_entity.name, prev_treelet_str=self.name,
#                                                  open_question=('default', text))
#         return text, conditional_state
#
#     @measure
#     def continue_response(self, base_response_result: ResponseGeneratorResult,
#                           new_entity: Optional[str] = None) -> ResponseGeneratorResult:
#         state = base_response_result.state
#         conditional_state = base_response_result.conditional_state
#
#         new_state = state.update(conditional_state)
#         if not (base_response_result.cur_entity or new_entity):
#             raise CantContinueResponseError("Neither base_response_result.cur_entity nor new_entity was given")
#         entity = new_entity or base_response_result.cur_entity
#         if len(new_state.entity_state[entity.name].highlights_used)>=2:
#             raise CantContinueResponseError("Already gave open response twice, not prompting anymore")
#
#         try:
#             text, new_conditional_state = self.get_prompt_question(new_state, entity)
#         except CantPromptError as e:
#             raise CantContinueResponseError(*e.args) from e
#
#         text = base_response_result.text + ' ' + text
#         conditional_state.prompt_handler = self.__repr__()
#         conditional_state.cur_doc_title = new_conditional_state.cur_doc_title
#         conditional_state.open_question = new_conditional_state.open_question
#         base_response_result.conditional_state = conditional_state
#         base_response_result.text = text
#         base_response_result.needs_prompt = False
#         base_response_result.cur_entity = entity
#         return base_response_result
#
#     @measure
#     def get_convpara_snippet(self, snippet:str, entity:WikiEntity) -> Optional[str]:
#         # if entity.name in CONVPARA_BLACKLISTED_ENTITIES:
#         #     logger.primary_info(f"{entity} blacklisted for convpara")
#         #     return None
#         paraphrases = ConvPara(self.rg.state_manager).get_paraphrases(background=snippet, entity=entity.name)
#         paraphrases = filter_and_log(lambda p: p.finished, paraphrases, "Paraphrases for snippet", "they were unfinished")
#         paraphrases = filter_and_log(lambda p: not contains_offensive(p.readable_text()), paraphrases, "Paraphrases for snippet", "contained offensive phrase")
#         #paraphrases = filter_and_log(lambda p: not did_you_know.execute(p.readable_text()), paraphrases, "Paraphrases for snippet", "contained did you know question")
#         if not paraphrases:
#             logger.warning(f"No good convparaphrases for snippet: \n {snippet}")
#             return None
#         paraphrases = sorted(paraphrases, key=lambda p: self.ngram_recall([p.readable_text()], snippet, 1),
#                              reverse=True)
#         text = paraphrases[0].readable_text()
#         if text[-1] not in ['.', '!', '?']:
#             text+='.'
#         return text
#
#     def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
#         state, utterance, response_types = self.get_state_utterance_response_types()
#         entity = state.cur_entity
#
#     # @measure
#     # def handle_prompt(self, state: State) -> ResponseGeneratorResult:
#     #     utterance = self.rg.state_manager.current_state.text.lower()
#     #     entity = self.rg.get_recommended_entity(state)
#     #     if not entity or entity.name not in state.entity_state:
#     #         raise CantRespondError("Recommended entity has changed")
#
#         # Check of some standard templates are matched - if so return appropriate response and handover
#         handover_response = None
#         if DontKnowTemplate().execute(utterance) is not None:
#             handover_response = self.choose(RESPONSE_TO_DONT_KNOW)
#         elif BackChannelingTemplate().execute(utterance) is not None:
#             handover_response = self.choose(RESPONSE_TO_BACK_CHANNELING)
#         elif NotThingTemplate().execute(utterance) is not None:
#             handover_response = self.choose(RESPONSE_TO_NOTHING_ANS)
#         elif ResponseType.NO in response_types:
#             handover_response = self.choose(HANDOVER_TEXTS)
#
#
#         if handover_response:
#             state.entity_state[entity.name].finished_talking=True
#             apology_response = ResponseGeneratorResult(text=handover_response,
#                                                        priority=ResponsePriority.STRONG_CONTINUE,
#                                                        needs_prompt=True, state=state, cur_entity=None,
#                                                        conditional_state=ConditionalState(
#                                                            prev_treelet_str=self.name,
#                                                            next_treelet_str=None
#                                                        ))
#             return apology_response
#
#         search_sections = self.search_highlights(state)
#         for selected_section in search_sections:
#             # This should not throw an error because there should at least be one suggested section that matches the option
#             # section_snippet = wiki_utils.clean_wiki_text(
#             #    wiki_utils.get_summary(selected_section.highlight, self.get_sentseg_fn()))
#             # I don't think we need to use get_summary because the highlights are usually short and well segmented
#             section_snippet = clean_wiki_text(selected_section.highlight)
#             overlapping_past_turn = self.rg.has_overlap_with_history(section_snippet)
#             if overlapping_past_turn:
#                 logger.info(f"Snippet : '{section_snippet}' for section: {selected_section.title} has high overlap "
#                             f"with history")
#                 non_overlapping_section_snippet = self.rg.remove_overlap(overlapping_past_turn, section_snippet)
#                 if len(non_overlapping_section_snippet.split(' ')) > 4:  # has at least 4 words, a heuristic
#                     logger.info(
#                         f"Using non-overlapping part {non_overlapping_section_snippet} of '{section_snippet}' despite overlap")
#                     section_snippet = non_overlapping_section_snippet
#                 else:
#                     logger.info(
#                         f"Discarding snippet : '{section_snippet}' for section: {selected_section.title}")
#                     continue
#             if chirpy.core.offensive_classifier.offensive_classifier.contains_offensive(section_snippet):
#                 logger.info(
#                     f"Most relevant section {selected_section.title} has an offensive phrase in the snippet: {section_snippet}")
#                 continue
#             logger.primary_info(
#                 f"Selecting {selected_section} to continue the conversation based on fuzzy matching with section text {section_snippet}")
#
#             convpara_snippet = self.get_convpara_snippet(section_snippet, entity)
#             if convpara_snippet:
#                 conditional_state = ConditionalState(cur_doc_title=entity.name, discussed_section=selected_section,
#                                                      prev_treelet_str=self.name,
#                                                      next_treelet_str=self.name,
#                                                      highlight_used=(section_snippet, selected_section),
#                                                      paraphrase=(section_snippet, convpara_snippet))
#                 base_response_result = ResponseGeneratorResult(text=convpara_snippet,
#                                                                priority=ResponsePriority.STRONG_CONTINUE,
#                                                                needs_prompt=True, state=state, cur_entity=entity,
#                                                                conditional_state=conditional_state)
#             else:
#
#                 if section_snippet[-1] not in ['.', '!', '?']:
#                     section_snippet += '.'
#                 conditional_state = ConditionalState(cur_doc_title=entity.name, discussed_section=selected_section,
#                                                      prev_treelet_str=self.name,
#                                                      next_treelet_str=None,
#                                                      highlight_used=(section_snippet, selected_section))
#                 base_response_result = ResponseGeneratorResult(text=section_snippet,
#                                                                priority=ResponsePriority.STRONG_CONTINUE,
#                                                                needs_prompt=True, state=state, cur_entity=entity,
#                                                                conditional_state=conditional_state)
#
#             all_article_links = {link for section in search_sections for link in section.section_links}
#             new_entity = None
#             for linked_span in self.rg.state_manager.current_state.entity_linker.all_linkedspans:
#                 if entity in linked_span.ents_by_priority:
#                     # If linked span links to current entity, don't consider it
#                     continue
#                 for wiki_entity in linked_span.ents_by_priority:
#                     if set(wiki_entity.redirects) & all_article_links and \
#                             any(anchor_text.lower() in section_snippet.lower() for anchor_text in list(wiki_entity.anchortext_counts.keys())[:10]):
#                         logger.primary_info(f"Detected {linked_span.span} in user utterance which matches {wiki_entity} in"
#                                             f"the section snippet {section_snippet}. Setting {wiki_entity.name} as the"
#                                             f"cur_entity")
#                         new_entity = wiki_entity
#                         break
#                 if new_entity:
#                     break
#
#             if new_entity:
#                 try:
#                     base_response_result = self.continue_response(base_response_result, new_entity)
#                 except CantContinueResponseError as e:
#                     pass
#             return base_response_result
#
#
#
#             # Picking the first intersecting
#         else:
#             response = get_random_fallback_neural_response(current_state=self.get_current_state())
#             if not response:
#                 logger.warning("No fallback neural responses were appropriate")
#                 chosen_response = self.choose(APOLOGY_TEXTS)
#                 state.entity_state[entity.name].finished_talking = True
#                 response_result = ResponseGeneratorResult(text=chosen_response,
#                                                           priority=ResponsePriority.STRONG_CONTINUE,
#                                                           needs_prompt=True, state=state, cur_entity=entity,
#                                                           conditional_state=ConditionalState(
#                                                               prev_treelet_str=self.name,
#                                                               next_treelet_str=None
#                                                           ))
#             else:
#                 if not (response[-1] in ['.', '!']):
#                     response += '.'
#                 logger.primary_info(f"Chose random neural fallback response {response} in Open question treelet")
#                 response_result = ResponseGeneratorResult(text=response,
#                                                           priority=ResponsePriority.STRONG_CONTINUE,
#                                                           needs_prompt=True, state=state, cur_entity=entity,
#                                                           conditional_state=ConditionalState(
#                                                               neural_fallback=response,
#                                                               prev_treelet_str=self.name,
#                                                               next_treelet_str=None
#                                                           ))
#
#             return response_result
#             # Don't try to ask the user what is interesting, because if all sections are offensive, then it is likely
#             # an inapproriate article
#     @measure
#     def get_can_start_response(self, state: State) -> ResponseGeneratorResult:
#         entity = self.rg.get_recommended_entity(state)
#         if not entity:
#             raise CantRespondError("No recommended entity")
#         if len(state.entity_state[entity.name].highlights_used)>=2:
#             raise CantRespondError("Already gave open response twice, not prompting anymore")
#         try:
#             text, conditional_state = self.get_prompt_question(state)
#         except CantPromptError as e:
#             raise CantRespondError(*e.args) from e
#         return ResponseGeneratorResult(text=text, priority=ResponsePriority.CAN_START,
#                                        state=state, cur_entity=entity, needs_prompt=False,
#                                        conditional_state=conditional_state)
#
#     @measure
#     def get_prompt(self, state: State) -> PromptResult:
#         text, conditional_state = self.get_prompt_question(state)
#         cur_entity = self.rg.get_recommended_entity(state)
#         prompt_type = PromptType.CURRENT_TOPIC
#         return PromptResult(text=text, prompt_type=prompt_type, state=state, cur_entity=cur_entity,
#                             conditional_state=conditional_state)
