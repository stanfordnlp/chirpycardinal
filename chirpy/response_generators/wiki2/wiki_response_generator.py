import os
import logging
from concurrent import futures

from typing import Optional, Set, Tuple
import random

from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_generator.neural_helpers import get_neural_fallback_handoff
from chirpy.annotators.blenderbot import BlenderBot
from chirpy.response_generators.wiki2.wiki_utils import token_overlap
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils
from chirpy.response_generators.wiki2.blacklists import CATEGORY_BLACK_LIST, ENTITY_BLACK_LIST

from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import *
from chirpy.response_generators.wiki2.treelets import *
from chirpy.response_generators.wiki2.wiki_helpers import *
from chirpy.response_generators.wiki2.wiki_infiller import *
# from chirpy.response_generators.wiki2.wiki_utils import *
from chirpy.response_generators.wiki2.pronouns import get_pronoun
from chirpy.core.smooth_handoffs import SmoothHandoff
from chirpy.response_generators.wiki2.response_templates.response_components import *
from chirpy.annotators.corenlp import Sentiment
from chirpy.response_generators.wiki2.state import State,ConditionalState, NO_UPDATE

from chirpy.response_generators.wiki2.treelets.takeover_treelet import WikiTakeOverTreelet # EDIT
from chirpy.response_generators.wiki2.treelets.handback_treelet import WikiHandBackTreelet # EDIT

logger = logging.getLogger('chirpylogger')

try:
    from chirpy.annotators.responseranker import ResponseRanker
    use_responseranker = True
except ModuleNotFoundError:
    logger.warning('ResponseRanker module not found, defaulting to original DialoGPT and GP T2 Rankers')
    from chirpy.annotators.dialogptranker import DialoGPTRanker
    from chirpy.annotators.gpt2ranker import GPT2Ranker
    use_responseranker = False

import threading


class WikiResponseGenerator(ResponseGenerator):
    name='WIKI'
    killable = True
    def __init__(self, state_manager) -> None:
        self.check_user_knowledge_treelet = CheckUserKnowledgeTreelet(self)
        self.acknowledge_user_knowledge_treelet = AcknowledgeUserKnowledgeTreelet(self)
        self.factoid_treelet = FactoidTreelet(self)
        self.intro_entity_treelet = IntroEntityTreelet(self)
        self.combined_til_treelet = TILTreelet(self)
        self.recheck_interest_treelet = RecheckInterestTreelet(self)
        self.discuss_article_treelet = DiscussArticleTreelet(self)
        self.discuss_section_treelet = DiscussSectionTreelet(self)
        self.discuss_section_further_treelet = DiscussSectionFurtherTreelet(self)
        self.get_opinion_treelet = GetOpinionTreelet(self)
        self.takeover_treelet = WikiTakeOverTreelet(self)   # EDIT
        self.handback_treelet = WikiHandBackTreelet(self)  # EDIT

        treelets = {t.name: t for t in [self.check_user_knowledge_treelet,
                                        self.acknowledge_user_knowledge_treelet, self.factoid_treelet,
                                        self.intro_entity_treelet, self.combined_til_treelet,
                                        self.discuss_article_treelet, self.discuss_section_treelet,
                                        self.discuss_section_further_treelet, self.get_opinion_treelet,
                                        self.takeover_treelet, self.handback_treelet]}

        super().__init__(state_manager, treelets=treelets, state_constructor=State, can_give_prompts=True,
                         conditional_state_constructor=ConditionalState,
                         transition_matrix=self.init_transition_matrix())

    def init_transition_matrix(self):
        matrix = {
            'intro_prompt': {
                ResponseType.NO: lambda: self.handle_rejection_response(),
                ResponseType.YES: lambda: random.choices([self.combined_til_treelet,self.check_user_knowledge_treelet,
                    self.factoid_treelet], weights=[0.45, 0.35, 0.2])[0].get_response(ResponsePriority.STRONG_CONTINUE)
            },
            self.check_user_knowledge_treelet.name: {
                ResponseType.YES: (self.acknowledge_user_knowledge_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.NO: (self.intro_entity_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: True: (self.acknowledge_user_knowledge_treelet, ResponsePriority.STRONG_CONTINUE)
            },
            self.get_opinion_treelet.name: {
                lambda state, response_types:
                (not response_types.isdisjoint({ResponseType.POS_SENTIMENT, ResponseType.NEUTRAL_SENTIMENT,
                                                ResponseType.APPRECIATIVE, ResponseType.KNOW_MORE, ResponseType.YES})):
                    (self.discuss_article_treelet, ResponsePriority.STRONG_CONTINUE),
            },
            self.acknowledge_user_knowledge_treelet.name: {
                ResponseType.NO: (self.recheck_interest_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.CONFUSED: (self.recheck_interest_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: True: (self.discuss_article_treelet, ResponsePriority.STRONG_CONTINUE)
            },
            self.factoid_treelet.name: {
                ResponseType.NO: (self.recheck_interest_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.CONFUSED: (self.recheck_interest_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: True: (self.discuss_article_treelet, ResponsePriority.STRONG_CONTINUE)
            },
            self.combined_til_treelet.name: {
                ResponseType.CONFUSED: (self.combined_til_treelet, ResponsePriority.STRONG_CONTINUE),
                ResponseType.NO: (self.recheck_interest_treelet, ResponsePriority.STRONG_CONTINUE),
                lambda state, response_types: True: (self.discuss_article_treelet, ResponsePriority.STRONG_CONTINUE)
            },
            self.recheck_interest_treelet.name: {
                ResponseType.NO: lambda: self.handle_rejection_response(),
                ResponseType.CONFUSED: lambda: self.handle_rejection_response(),
                ResponseType.YES: (self.discuss_article_treelet, ResponsePriority.STRONG_CONTINUE)
            },
            self.discuss_article_treelet.name: {
                ResponseType.NO: lambda: self.handle_rejection_response(),
                lambda state, response_types: True: (self.discuss_section_treelet, ResponsePriority.STRONG_CONTINUE)
            },
            self.discuss_section_further_treelet.name: {
                ResponseType.NO: lambda: self.handle_rejection_response(),
                ResponseType.YES: (self.discuss_article_treelet, ResponsePriority.STRONG_CONTINUE) # TODO handle specific section requests,
            }
        }
        return matrix

    def identify_response_types(self, utterance) -> Set[ResponseType]:
        response_types = super().identify_response_types(utterance)

        if user_is_confused(self, utterance): response_types.add(ResponseType.CONFUSED)
        if is_neg_sentiment(self, utterance): response_types.add(ResponseType.NEG_SENTIMENT)
        if is_pos_sentiment(self, utterance): response_types.add(ResponseType.POS_SENTIMENT)
        if is_neutral_sentiment(self, utterance): response_types.add(ResponseType.NEUTRAL_SENTIMENT)
        if is_opinion(self, utterance): response_types.add(ResponseType.OPINION)
        if is_appreciative(self, utterance): response_types.add(ResponseType.APPRECIATIVE)

        if response_types.isdisjoint({ResponseType.COMPLAINT, ResponseType.DISINTERESTED}):
            # to counter false positives, e.g. "that is not interesting"
            if user_wants_to_know_more(self, utterance):
                response_types.add(ResponseType.KNOW_MORE)

        if is_personal_disclosure(self, utterance): response_types.add(ResponseType.PERSONAL_DISCLOSURE)
        if user_disagees(self, utterance):
            response_types.add(ResponseType.DISAGREEMENT)
        else: # check is necessary to prevent false positives
            if user_agrees(self, utterance): response_types.add(ResponseType.AGREEMENT)
        if is_no_to_sections(self, utterance): response_types.add(ResponseType.NO)
        if starts_with_what(self, utterance): response_types.add(ResponseType.STARTS_WITH_WHAT)

        return response_types

    def handle_question(self):
        state, utterance, response_types = self.get_state_utterance_response_types()

        # if ResponseType.STARTS_WITH_WHAT in response_types: # what is carabinieri? TODO not currently working
        #     logger.primary_info("Asked what is question")
        #     entity = self.get_recommended_entity(initiated_this_turn=True)
        #     logger.primary_info(f"entity is {entity}")
        #     if entity is not None:
        #         state.cur_entity = entity
        #         return self.get_intro_treelet_response()
        if ResponseType.KNOW_MORE in response_types: # do not handle questions where the user wants to know more
            return None
        if state.prev_treelet_str == self.discuss_section_treelet.name:
            return self.discuss_section_further_treelet.get_question_response()

        if state.prev_treelet_str == self.factoid_treelet.name:
            return self.factoid_treelet.get_question_response()

    def handle_change_topic(self):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if state.prev_treelet_str == self.discuss_article_treelet.name:
            return None
        else:
            return False

    def handle_current_entity(self, priority=ResponsePriority.CAN_START):
        current_entity = self.get_recommended_entity(initiated_this_turn=True)
        priority = self._get_priority_from_answer_type() 
        logger.primary_info(f"Wiki is handling current entity: {current_entity} with priority: {priority}")
        answer_type = self.get_answer_type()
        logger.info(f"Answer type is: {answer_type}")
        POS_NAV = self.get_navigational_intent_output().pos_intent
        logger.info(f"POSNAV is {POS_NAV}")
        logger.info(f"Current entity is {current_entity}")
        #  # ignored; WIKI should always be CAN_START...
        # import pdb; pdb.set_trace()
        if current_entity:
            self.state.cur_entity = current_entity
            if POS_NAV:
                treelet = random.choices([self.check_user_knowledge_treelet, self.factoid_treelet], weights=[0.8, 0.2])[0]
                logger.primary_info(f"Choosing a treelet at random for POS_NAV: {treelet.name}")
                return treelet.get_response(priority)
            if answer_type == AnswerType.QUESTION_HANDOFF: # what's a country you would like to visit?
                treelet = random.choices([self.combined_til_treelet, self.factoid_treelet], weights=[0.5, 0.5])[0]
                return treelet.get_response(priority)
            if answer_type == AnswerType.STATEMENT:
                return self.combined_til_treelet.get_response(priority=ResponsePriority.CAN_START)

    def finish_talking(self, entity_name):
        self.state.entity_state[entity_name].finished_talking = True

    def has_overlap_with_history(self, utterance, threshold = 0.5):
        for response_text in self.state_manager.current_state.history:
            percentage_overlap = token_overlap(utterance, response_text)
            if percentage_overlap >= threshold:
                return response_text
        return None

    def get_recommended_entity(self, state=None, initiated_this_turn=True):
        if state is not None:
            pass
        else:
            state = self.state
        entity = self.get_current_entity(initiated_this_turn)

        if initiated_this_turn and not entity and self.get_last_active_rg() == 'TRANSITION':
            entity = self.get_current_entity()
        # import pdb; pdb.set_trace()
        if entity:
            if entity.is_category:
                logger.primary_info(f"Recommended entity {entity} is a category, not using it for WIKI")
            elif entity.name in ENTITY_BLACK_LIST or wiki_utils.remove_parens(entity.name) in ENTITY_BLACK_LIST:
                logger.primary_info(f"Recommended entity {entity} is blacklisted for WIKI")
            elif entity.name in state.entity_state and state.entity_state[entity.name].finished_talking:
                logger.primary_info(f"Wiki has finished talking about recommended entity {entity}")
            else:
                logger.primary_info(f"Recommending entity {entity}: {entity.name}.")
                return entity
        logger.primary_info("Wiki didn't find an entity; returning.")
        return None



    def get_entity(self, state: State) -> UpdateEntity:
        # change to next_trelet_str
        utterance = self.utterance
        entity = self.get_recommended_entity(state)
        if not entity:
            logger.primary_info("WIKI's get_entity function found no cur_entity and won't change the cur_entity either")
            return UpdateEntity(False)
        if state.next_treelet_str == self.discuss_section_treelet.name and wiki_utils.any_section_title_matches(utterance, entity):
            return UpdateEntity(True, entity)
        # if state.next_treelet_str == self.open_question_treelet.name and \
        #         len(self.open_question_treelet.search_highlights(state)) > 0:
        #     return UpdateEntity(True, entity)
        #
        # if (prompt_handler == 'Handle Section Treelet (WIKI)' and
        #         self.all_treelets['Handle Section Treelet (WIKI)'].any_section_title_matches(state)) or \
        #     (prompt_handler == 'Open Question Treelet (WIKI)' and
        #             len(self.all_treelets['Open Question Treelet (WIKI)'].search_highlights(state))>0):
        #         return UpdateEntity(True, self.get_recommended_entity(state))

        return UpdateEntity(False)

    def handle_smooth_handoff(self) -> Optional[PromptResult]:
        cur_entity = self.get_current_entity(initiated_this_turn=False)
        self.state.cur_entity = cur_entity
        handoff = self.get_smooth_handoff()
        if handoff == SmoothHandoff.ONE_TURN_TO_WIKI_GF:
            return self.intro_entity_treelet.get_prompt()

        if handoff == SmoothHandoff.PETS_TO_WIKI:
            text = self.choose(ENTITY_INTRODUCTION_TEMPLATES).format(entity_name=cur_entity.name)
            return PromptResult(text=text,
                            prompt_type=PromptType.FORCE_START,
                            state=self.state,
                            cur_entity=cur_entity,
                            conditional_state=ConditionalState(
                                prev_treelet_str='intro_prompt',
                                next_treelet_str='transition'
                            ))
        elif handoff == SmoothHandoff.NEURALCHAT_TO_WIKI:
            return self.factoid_treelet.get_prompt()
            # [neural_chat] i'm glad you like the book. [wiki] Speaking of Pride and Prejudice...
            # manual_acknowledgement = f"Speaking of {cur_entity.name}, "
            # self.get_infilling_statement(cur_entity, )

    def get_untalked_entity(self):
        state = self.state
        untalked_entities = self.get_entities()['user_mentioned_untalked']
        for entity in reversed(untalked_entities):
            if (not entity.is_category) and (not (entity in ENTITY_BLACK_LIST)) and \
                    (not (entity.name in state.entity_state or state.entity_state[entity.name].finished_talking)):
                logger.primary_info(f"Found {entity} in entity_tracker.user_mentioned_untalked, the latest entity"
                                    f"for Wiki to not have finished talking")
                return entity

    def get_intro_prompt(self) -> Optional[PromptResult]:
        turns_since_last_active = self.get_current_state().turns_since_last_active

        if len(self.get_conversation_history()) // 2 < 50:
            if not (turns_since_last_active['WIKI'] >= 15 and turns_since_last_active['TRANSITION'] >= 8):
                return self.emptyPrompt()
        else: # decrease intervals between transition prompts once the conversation is long
            if not (turns_since_last_active['WIKI'] >= 8 and turns_since_last_active['TRANSITION'] >= 4):
                return self.emptyPrompt()

        state, utterance, response_types = self.get_state_utterance_response_types()
        latest_untalked_entity = self.get_untalked_entity()
        if latest_untalked_entity is not None:
            state.cur_entity = latest_untalked_entity
            text = self.choose(ENTITY_INTRODUCTION_TEMPLATES).format(entity_name=latest_untalked_entity.talkable_name)
            return PromptResult(text=text,
                            prompt_type=PromptType.GENERIC,
                            state=state,
                            cur_entity=latest_untalked_entity,
                            conditional_state=ConditionalState(
                                prev_treelet_str='intro_prompt',
                                next_treelet_str='transition'
                            ))

    def _execute_infiller(self, input_data):
        infiller_cache = self.get_cache('infiller')
        if infiller_cache is not None:
            # assert not include_acknowledgements, "Infiller cache should only be set while prompting"
            logger.primary_info(f"Using the infiller cache.")
            return infiller_cache
        if os.environ['usecolbert']:
            infiller_results = call_colbertinfiller(
                input_data.get('tuples'),
                input_data.get('sentences'),
                input_data.get('max_length'),
                input_data.get('contexts', tuple()),
                input_data.get('prompts', tuple()),
            )
        else:
            infiller_results = call_infiller(
                input_data.get('tuples'),
                input_data.get('sentences'),
                input_data.get('max_length'),
                input_data.get('contexts', tuple()),
                input_data.get('prompts', tuple()),
            )
        return infiller_results

    def _select_best_response(self, utterance, responses, contexts, prompts, acknowledgements=None) -> Tuple[str, str]:
        """

        :param utterance:
        :param responses:
        :param contexts:
        :param prompts:
        :param acknowledgements: an optional list of acknowledgements to rank
        :return: Returns top_res, top_ack (optional)
        """
        ranker = ResponseRanker(self.state_manager)
        top_ack = None
        if acknowledgements:
            scores = get_scores(ranker, utterance, acknowledgements + responses)
            if scores['error']:
                logger.primary_info("Scores failed")
                return None, None
            ack_scores, response_scores = wiki_utils.split_dict_with_length(scores, len(acknowledgements))
            logger.primary_info(f"After splitting: {ack_scores} {response_scores}")

            ack_gpt_scores = ack_scores['score']
            ack_dialogpt_scores = ack_scores['updown']
            ack_scores = [(a - b*2) for a, b in zip(ack_gpt_scores, ack_dialogpt_scores)]
            logger.primary_info(f"ack_scores: {ack_scores}")
            top_ack = acknowledgements[ack_scores.index(min(ack_scores))].strip()
            # TODO: better handling of terminal punctuation
            if not top_ack.endswith('.') and not top_ack.endswith('?'): top_ack += '.'
        else:
            response_scores = get_scores(ranker, utterance, responses)
            if response_scores is None or response_scores['error']:
                logger.primary_info("Scores failed")
                return None, None

        res_gpt_scores = [-math.log(x) for x in response_scores['score']]
        res_dialogpt_scores = response_scores['updown']
        res_scores = [(dialogpt_score - gpt_score*0.25) for gpt_score, dialogpt_score in zip(res_gpt_scores, res_dialogpt_scores)]
        logger.primary_info(f"res_scores: {res_scores}")
        logger.primary_info('\n'.join([f"{sc:.3f} ({gpt_sc:.3f} {dgpt_sc:.3f}) {utt} [{context}]"
                                       for sc, gpt_sc, dgpt_sc, utt, context in zip(res_scores, res_gpt_scores, res_dialogpt_scores, responses, contexts)]))

        best_completion_idx = res_scores.index(max(res_scores))
        top_res = responses[best_completion_idx].strip()
        # TODO: better handling of terminal punctuation
        if not top_res.endswith('.') and not top_res.endswith('?'): top_res += '.'

        logger.primary_info(f"Wiki infiller context used: {contexts[best_completion_idx]}")
        logger.primary_info(f"Wiki infiller template used: {prompts[best_completion_idx]}")

        return top_res, top_ack

    def get_wiki_sentences(self, cur_entity):
        sections = wiki_utils.get_text_for_entity(cur_entity.name)
        sentences = wiki_utils.get_sentences_from_sections_tfidf(sections, self.state_manager,
                                                                 first_turn=self.active_last_turn())
        return sentences

    def _get_infilling_ack_components(self, top_da):
        """

        :param top_da: top dialog act
        :return:
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        infilling_ack_context = None
        infilling_ack_prompts = None

        if top_da in ['statement', 'opinion', 'comment']:
            # agree with user
            infilling_ack_context = utterance
            infilling_ack_prompts = STATEMENT_ACKNOWLEDGEMENT_TEMPLATES
        elif ResponseType.POS_SENTIMENT in response_types or ResponseType.APPRECIATIVE in response_types:
            infilling_ack_context = self.get_conversation_history()[-1]
            infilling_ack_prompts = APPRECIATION_ACKNOWLEDGEMENT_TEMPLATES
        return infilling_ack_context, infilling_ack_prompts

    def get_top_dialogact(self):
        pred_proba = self.get_dialogact_probdist()
        top_da = max(pred_proba, key=lambda act: pred_proba[act] if act != 'abandon' else -1) # max of all except abandon
        return top_da

    def get_infilling_statement_from_wiki_section(self, entity: WikiEntity, section: wiki_utils.WikiSection,
                                                  neural_ack: bool = False, infill_ack: bool = False):
        utterance = self.utterance
        text = section.section_text
        cur_entity = entity
        sentences = wiki_utils.get_sentences(text, self.state_manager)
        specific_responses = get_section_templates(section.title)
        acknowledgements = None
        execute_neural = None

        input_data = {
            'tuples': tuple((q[0], tuple(q[1])) for q in specific_responses),
            'sentences': tuple(s.strip() for s in sentences), #TODO tuple(s.strip().strip('.') for s in sentences),
            'max_length': 40
        }

        thread = threading.currentThread()
        should_kill = getattr(thread, "killable", False)
        if should_kill:
            logger.primary_info(f"Infiller interior call detected to be running in a killable thread.")
        is_done = getattr(thread, "isKilled", False)

        if infill_ack:
            top_da = self.get_top_dialogact()
            infilling_ack_context, infilling_ack_prompts = self._get_infilling_ack_components(top_da)
            input_data.update({
                'contexts': tuple([infilling_ack_context] * len(infilling_ack_prompts)),
                'prompts': tuple(infilling_ack_prompts),
            })
        elif neural_ack:
            MAX_HISTORY_UTTERANCES = 3
            history = self.state_manager.current_state.history[-(MAX_HISTORY_UTTERANCES - 1):]   # TODO: if we're changing topic, don't use history
            def execute_neural():
                responses, _ = BlenderBot(self.state_manager).execute(input_data={'history': history+[utterance]})
                return responses

        def initializer(killable: bool):
            threading.currentThread().killable = killable
            threading.currentThread().isKilled = is_done

        with futures.ThreadPoolExecutor(max_workers=2, initializer=initializer, initargs=(should_kill,)) as executor:
            if execute_neural:
                neural_future = executor.submit(execute_neural)
            infiller_future = executor.submit(self._execute_infiller, input_data)

        if execute_neural:
            acknowledgements = neural_future.result()

        infiller_results = infiller_future.result()

        if infiller_results['error']:
            logger.primary_info("Infiller failed")
            return None, None

        if infill_ack:
            # if need_to_infill_acknowledgements:
            # Cut up the responses, if we asked for acknowledgement generation
            # import pdb; pdb.set_trace()
            ack_results, infiller_results = wiki_utils.split_dict_with_length(infiller_results, len(infilling_ack_prompts))
            acknowledgements = ack_results['completions']

        if acknowledgements is not None:
            acknowledgements = filter_responses(self, acknowledgements, cur_entity.name)
            logger.primary_info(f"Got acknowledgements: {acknowledgements}")

        self.set_cache('infiller', infiller_results)

        responses = infiller_results['completions']
        responses = filter_responses(self, responses, cur_entity.name)

        logger.primary_info(f"Got responses: {responses}")
        if len(responses) == 0:
            return None, None
        prompts = infiller_results['prompts']
        contexts = infiller_results['contexts']

        return self._select_best_response(utterance, responses, contexts, prompts, acknowledgements)


    def get_infilling_statement(self, entity: Optional[WikiEntity] = None, neural_ack=False, infill_ack=False) -> Tuple[Optional[str], Optional[str]]:
        """
        Get an infilled statement, optionally with acknowledgement infilled as well.

        :param entity:
        :return: (top response, top acknowledgement)
        """

        state, utterance, response_types = self.get_state_utterance_response_types()
        cur_entity = entity

        ## STEP 1: Get Wiki sections and the sentences from those sections
        sentences = self.get_wiki_sentences(cur_entity)
        logger.primary_info(f"Wiki sentences are: {sentences}")
        if len(sentences) < 4:
            logger.primary_info("Infiller does not have enough sentences to work with")
            return None, None

        ## Step 2a: Get the relevant templates for the entity
        # Retrieve questions, text.
        specific_responses, best_ent_group = get_templates(cur_entity)
        if specific_responses is None:
            return None, None
        # specific_responses example:
        # [["In my opinion, the best place for [clothing] is [store].", ["clothing", "fashion", "retailer", "dress", "suits"]]]
        ## Step 2b:
        # We replace pronouns on second one onwards.
        # Note that this is irrelevant for the prompt case, since we reconstruct the prompts later anyway.
        pronouns = get_pronoun(best_ent_group, sentences)
        prompt_to_pronoun_prompt = {prompt: replace_entity_placeholder(prompt, pronouns, cur_entity.talkable_name, omit_first=True)
                                    for (prompt, _) in specific_responses}
        specific_responses = [(prompt_to_pronoun_prompt[a], b) for (a, b) in specific_responses]
        # logger.primary_info(f"After replacement: {specific_questions} {type(specific_questions[0])}")
        specific_responses = [q for q in specific_responses if q[0] not in state.entity_state[cur_entity.name].templates_used]

        input_data = {
            'tuples': tuple((q[0], tuple(q[1])) for q in specific_responses),
            'sentences': tuple(s.strip().strip('.') for s in sentences), # TODO tuple(s.strip().strip('.') for s in sentences),
            'max_length': 40
        }

        execute_neural = None
        acknowledgements = None

        if infill_ack:
            top_da = self.get_top_dialogact()
            infilling_ack_context, infilling_ack_prompts = self._get_infilling_ack_components(top_da)
            input_data.update({
                'contexts': tuple([infilling_ack_context] * len(infilling_ack_prompts)),
                'prompts': tuple(infilling_ack_prompts),
            })
        elif neural_ack:
            MAX_HISTORY_UTTERANCES = 3
            history = self.state_manager.current_state.history[-(MAX_HISTORY_UTTERANCES - 1):]   # TODO: if we're changing topic, don't use history
            def execute_neural():
                responses, _ = BlenderBot(self.state_manager).execute(input_data={'history': history+[utterance]})
                return responses

        ### BEGIN THREADING ###
        thread = threading.currentThread()
        should_kill = getattr(thread, "killable", False)
        if should_kill:
            logger.primary_info(f"Infiller interior call detected to be running in a killable thread.")
        is_done = getattr(thread, "isKilled", False)

        def initializer(killable: bool):
            threading.currentThread().killable = killable
            threading.currentThread().isKilled = is_done

        with futures.ThreadPoolExecutor(max_workers=2, initializer=initializer, initargs=(should_kill,)) as executor:
            if execute_neural:
                neural_future = executor.submit(execute_neural)
            infiller_future = executor.submit(self._execute_infiller, input_data)
        ### END THREADING ###

        if execute_neural:
            acknowledgements = neural_future.result()

        infiller_results = infiller_future.result()

        if infiller_results['error']:
            logger.primary_info("Infiller failed")
            return None, None

        if infill_ack:
            # if need_to_infill_acknowledgements:
            # Cut up the responses, if we asked for acknowledgement generation
                # import pdb; pdb.set_trace()
            ack_results, infiller_results = wiki_utils.split_dict_with_length(infiller_results, len(infilling_ack_prompts))
            acknowledgements = ack_results['completions']

        if acknowledgements is not None:
            acknowledgements = filter_responses(self, acknowledgements, cur_entity.name)
            logger.primary_info(f"Got acknowledgements: {acknowledgements}")

        self.set_cache('infiller', infiller_results)

        responses = infiller_results['completions']
        prompts = infiller_results['prompts']

        # TODO check this -- why is this only done for smooth transition? ANS: It will replace the first occurrence of entity with the pronoun.
        # if smooth_transition:
        #     logger.primary_info(f"Responses before pronouns treatment: {responses}")
        #     pronouns = get_pronoun(best_ent_group, sentences)
        #     pronoun_prompt_to_prompt = {b: a for (a, b) in prompt_to_pronoun_prompt.items()}
        #     responses = [revert_to_entity_placeholder(response, cur_entity.name, pronoun_prompt_to_prompt[prompt]) for response, prompt in zip(responses, prompts)]
        #     responses = [replace_entity_placeholder(response, pronouns) for response in responses]
        #     logger.primary_info(f"Responses after pronouns treatment: {responses}")

        responses = filter_responses(self, responses, cur_entity.name)

        logger.primary_info(f"Got responses: {responses}")

        prompts = infiller_results['prompts']
        contexts = infiller_results['contexts']

        return self._select_best_response(utterance, responses, contexts, prompts, acknowledgements)

    def update_state_if_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        state = super().update_state_if_chosen(state, conditional_state)

        logger.primary_info(f"Conditional_state: {conditional_state}")
        # update the dict
        if conditional_state.cur_doc_title != NO_UPDATE:
            entity_name = conditional_state.cur_doc_title
            entity_state = state.entity_state[entity_name]

            if conditional_state.open_question != NO_UPDATE:
                return_type, question, answer = conditional_state.open_question
                if return_type in entity_state.open_questions_asked:
                    logger.error(f"Previously asked {entity_state.open_questions_asked}, but asking new question {conditional_state.open_question}")
                entity_state.open_questions_asked[return_type] = question

            if conditional_state.til_used != NO_UPDATE:
                if conditional_state.til_used not in entity_state.tils_used:
                    entity_state.tils_used.append(conditional_state.til_used)

            if conditional_state.highlight_used != NO_UPDATE:
                snippet, wiki_section = conditional_state.highlight_used
                wiki_section = wiki_section.purge_section_text()
                entity_state.highlights_used.append((snippet, wiki_section))

            if conditional_state.discussed_section != NO_UPDATE:
                purged_last_discussed_section = conditional_state.discussed_section.purge_section_text()
                entity_state.last_discussed_section = purged_last_discussed_section
                entity_state.discussed_sections.append(conditional_state.discussed_section.purge_section_text())

            if conditional_state.suggested_sections != NO_UPDATE:
                entity_state.suggested_sections.extend([s.purge_section_text() for s in conditional_state.suggested_sections])

            if conditional_state.paraphrase != NO_UPDATE:
                original_text, paraphrased_text = conditional_state.paraphrase
                entity_state.conv_paraphrases[original_text].append(paraphrased_text)
            if conditional_state.neural_fallback != NO_UPDATE:
                entity_state.neural_fallbacks_used.append(conditional_state.neural_fallback)
            if conditional_state.template_used != NO_UPDATE:
                entity_state.templates_used.append(conditional_state.template_used)
            if conditional_state.context_used != NO_UPDATE:
                entity_state.contexts_used.append(conditional_state.context_used)

        return state

    def update_state_if_not_chosen(self, state: State, conditional_state: Optional[ConditionalState], rg_was_taken_over=False) -> State:    # EDIT
        state = super().update_state_if_not_chosen(state, conditional_state)
        state.cur_doc_title = None
        state.suggested_sections = []
        state.discussed_section = None
        state.prompted_options = []

        state.til_used = None
        state.highlight_used = None
        state.paraphrase = None

        state.open_question = None
        state.neural_fallback = None
        state.template_used = None
        state.context_used = None

        return state

    def get_takeover_response(self):  # EDIT
        logger.info("WIKI TAKEOVER")
        return self.takeover_treelet.get_response(ResponsePriority.FORCE_START)