from chirpy.core.response_generator.treelet import Treelet
import logging
from typing import Optional, Tuple
from chirpy.annotators.convpara import ConvPara, select_fused_pcmi_h_candidate
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.latency import measure
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.util import filter_and_log, contains_phrase, get_ngrams
from chirpy.response_generators.wiki2.state import State, CantRespondError, ConditionalState
from chirpy.response_generators.wiki2.response_templates.response_components import OFFER_TIL
# from chirpy.response_generators.wiki2.treelets.abstract_treelet import HANDOVER_TEXTS, CONVPARA_BLACKLISTED_ENTITIES
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils
from chirpy.response_generators.wiki2.wiki_helpers import *
from copy import deepcopy
from chirpy.response_generators.wiki2.wiki_utils import token_overlap
import random

logger = logging.getLogger('chirpylogger')


class TILTreelet(Treelet):
    """
    TIL treelet gives a interesting TIL about the entity if possible.
     It used to try to give a convpara version of that TIL, but that did not work out so hot
    """
    name = "wiki_TIL_treelet"

    def get_base_til(self, entity: str) -> Optional[Tuple[str, str, str]]:
        """Get a valid TIL that is safe to be served

        :param entity: the entity we are getting TIL for
        :type entity: str
        :return: A TIL randomly chosen from a bunch of TILs. Each TIL is of the form (text, doc_title, section_title)
        :rtype: Optional[Tuple[str, str, str]]
        :rtype: Optional[Tuple[str, str, str]]

        """
        state = self.rg.state
        if entity in state.entity_state and len(state.entity_state[entity].tils_used) >= 2:
            logger.info(f"Already used 2 TILs for f{entity}, not reading out any more")
            return None
        tils = deepcopy(wiki_utils.get_til_title(entity))
        used_tils = state.entity_state[entity].tils_used
        if not tils:
            logger.info(f"Wiki found no TILs for {entity}")
            return None
        overlap_threshold = 0.75
        random.shuffle(tils)
        for til_text, doc_title, section_title in tils:
            overlapping_response = self.rg.has_overlap_with_history(til_text, threshold=overlap_threshold)
            #TODO-future: This should use TFIDF
            overlapping_til = any(token_overlap(til_text, c)>overlap_threshold for c in used_tils)
            if not overlapping_response and not overlapping_til:
                break
        else:
            logger.info("All TILs have either been used, or have a high overlap with previous utterances")
            return None
        return til_text, doc_title, section_title


    def get_paraphrases(self, background, entity, higher_unigram_recall, statement_or_question):
        conv_para = ConvPara(self.rg.state_manager)
        paraphrases = conv_para.get_paraphrases(background=background, entity=entity.name)
        if paraphrases is None: paraphrases = []
        paraphrases = filter_and_log(lambda p: p.finished, paraphrases, "Paraphrases for TIL", "they were unfinished")
        paraphrases = filter_and_log(lambda p: not contains_offensive(p.readable_text()), paraphrases, "Paraphrases for TIL", "contained offensive phrase")

        did_you_know = DidYouKnowQuestionTemplate()
        if statement_or_question:
            if statement_or_question == 'question':
                paraphrases = sorted(paraphrases,
                                     key=lambda p: did_you_know.execute(p.readable_text()), reverse=True)
            else:
                paraphrases = sorted(paraphrases,
                                     key=lambda p: not did_you_know.execute(p.readable_text()), reverse=True)
        #if preferences.higher_unigram_recall:
        #    generations_for_other_tils = state.entity_state[entity.name].conv_paraphrases[til_text] if til_text in state.entity_state[entity.name].conv_paraphrases else []
        #    paraphrases = sorted(paraphrases, key=lambda p: self.ngram_recall([p.readable_text()] + generations_for_other_tils, til_text, 1), reverse=True)
        return paraphrases

    def get_til_text(self, entity: WikiEntity, higher_unigram_recall: bool = False,
                     statement_or_question: str = None):
        """
        Gets a TIL text. Returns the original TIL and the paraphrased version.
        Returns None if no TIL is available.

        Has infrastructure for giving convpara responses, but they are currently commented out.

        :param entity:
        :param higher_unigram_recall:
        :param statement_or_question: favor "statement" or "question"
        :return: Tuple of (original TIL, paraphrased TIL text)
        """
        # if entity.name in CONVPARA_BLACKLISTED_ENTITIES:
        #     logger.primary_info(f'{entity.name} blacklisted for convpara')
        #     return None
        til_response = self.get_base_til(entity.name)
        if not til_response:
            logger.primary_info("No TIL is available.")
            return None
        base_til, _, _ = til_response

        # paraphrases = self.get_paraphrases(background=base_til, entity=entity,
        #                                    higher_unigram_recall=higher_unigram_recall,
        #                                    statement_or_question=statement_or_question)
        #
        # if not paraphrases:
        #     logger.primary_info("No paraphrased TILs exist.")
        #     return base_til, None

        # select paraphrase
        # experiments = self.get_experiments()
        # selection_strategy = self.get_experiment_by_lookup('convpara_selection_strategy')
        # if selection_strategy == 'fused-pcmi':
        #     selected_paraphrase = select_fused_pcmi_h_candidate(paraphrases)
        # elif selection_strategy == 'max-pmi':
        #     selected_paraphrase = max(paraphrases, key=lambda p: p.pmi)
        #
        # if 'convpara_selection_strategy' not in experiments.experiments_aux_data:
        #     experiments.experiments_aux_data['convpara_selection_strategy'] = []
        #
        # experiments.experiments_aux_data['convpara_selection_strategy'].append({
        #     'paraphrases': paraphrases,
        #     'selected_paraphrase': selected_paraphrase
        # })
        #
        # paraphrased_text = selected_paraphrase.readable_text()
        # if paraphrased_text[-1] not in ['.', '!', '?']:
        #     paraphrased_text += '.'
        # logger.primary_info("Successfully generated paraphrases and selected one.")

        # Caleb: This doesn't work that well. Just working with base TIL
        # logger.primary_info(f"TIL text: {base_til} \n ConvPara output: {paraphrased_text}")
        logger.primary_info(f"TIL text: {base_til} \n")

        return base_til #, paraphrased_text

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        entity = state.cur_entity

        if ResponseType.CONFUSED in response_types and state.prev_treelet_str == self.name:
            # last_til = state.entity_state[entity.name].tils_used[-1]
            # text = self.choose(original_til_templates(apologize=True, original_til=last_til))
            # conditional_state = ConditionalState(
            #     cur_doc_title=entity.name,
            #     prev_treelet_str=self.name,
            #     next_treelet_str='transition',
            #     til_used=last_til)
            #
            # # state.convpara_measurement['codepath'] = 'apologize_with_original_phrasing_for_unclear_paraphrase'
            # response_result = ResponseGeneratorResult(text=text, priority=priority,
            #                                           needs_prompt=True, state=state, cur_entity=entity,
            #                                           conditional_state=conditional_state)
            # logger.primary_info(f'WIKI is responding with an apology and a non-paraphrased version of the '
            #                     f'previous TIL entity {entity}')
            # return response_result
            return self.rg.recheck_interest_treelet.get_response()

        else:
            base_til = self.get_til_text(entity)
            if base_til is not None:
                cleaned_wiki_text = wiki_utils.clean_wiki_text(base_til) # if paraphrased_text is None else wiki_utils.clean_wiki_text(paraphrased_text)
                # if paraphrased_text is not None:
                offer_til = random.choice(OFFER_TIL)
                cleaned_wiki_text = cleaned_wiki_text.lower()
                if cleaned_wiki_text.startswith('that '): offer_til = offer_til.replace(' that', '')
                ack = random.choice([
                    f'Ah, {entity.talkable_name}.',
                    f'Oh, {entity.talkable_name}.'
                ])
                ack = ack if len(ack) <= 4 else '' # no ack for entities with long names

                return ResponseGeneratorResult(
                    text=f"{ack} {offer_til} {cleaned_wiki_text}. What do you think about that?",
                    priority=priority,
                    state=self.rg.state, needs_prompt=False, cur_entity=entity,
                    conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                       next_treelet_str='transition', cur_doc_title=entity.name,
                                                       til_used=base_til, paraphrase=(base_til, ""))
                                                       #paraphrase=(base_til, None if paraphrased_text is None else cleaned_wiki_text))
                )
            else:
                if kwargs.get('redirect', False):
                    return self.rg.check_user_knowledge_treelet.get_response(priority=priority)
                else:
                    return self.rg.factoid_treelet.get_response(priority=priority, redirect=True)
