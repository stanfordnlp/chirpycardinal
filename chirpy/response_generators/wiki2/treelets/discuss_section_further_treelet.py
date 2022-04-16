from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult, PromptType
from chirpy.response_generators.wiki2.state import ConditionalState
from chirpy.response_generators.wiki2.response_templates.response_components import *
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION
from chirpy.response_generators.wiki2.treelets.open_questions import OPEN_QUESTIONS_DICTIONARY
import logging
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.util import filter_and_log
import random
from chirpy.response_generators.wiki2.wiki_utils import WikiSection
from chirpy.response_generators.wiki2.wiki_helpers import ResponseType
import editdistance
import chirpy.core.offensive_classifier.offensive_classifier
# from chirpy.annotators.coqa import CoQA
from chirpy.annotators.sentseg import NLTKSentenceSegmenter
from chirpy.core.regex.response_lists import *
from chirpy.response_generators.neural_fallback.neural_helpers import get_random_fallback_neural_response


logger = logging.getLogger('chirpylogger')
HANDOVER_TEXTS = ["Alright!", "Okay! Moving on.", "Sounds good!"]

def open_answer_prompts(entity: WikiEntity):
    prompts = [
        f"I'm curious to hear what you think about {entity.talkable_name}?",
        f"Do you have any thoughts on {entity.talkable_name}?"
    ]
    return prompts

class DiscussSectionFurtherTreelet(Treelet):
    """
    Discuss a specific Wiki section further after user has given a response, either by answering a question,
    elaborating on the section, or giving an infilled personal opinion/observation
    """
    name = "wiki_discuss_section_further_treelet"

    # def get_question_response(self):
    #     state, utterance, response_types = self.get_state_utterance_response_types()
    #     qa_module = CoQA(self.rg.state_manager)
    #     cur_entity = state.cur_entity
    #     answers = qa_module.execute(utterance, state.discussed_section.section_text, 3)
    #     logger.primary_info(f"Discuss section further treelet got answers {answers}")
    #     if len(answers) != 0:
    #         best_answer = [a for a in answers if a[0] != ''][0][0].split(' [SEP] ')[-1]        # ignore empty
    #         sentseg = NLTKSentenceSegmenter(self.rg.state_manager)
    #         answer = list(sentseg.execute(best_answer))[0]
    #         prefix = random.choice(["If I understand correctly", "From what I understand", "If I'm not mistaken"])
    #         return ResponseGeneratorResult(text=f"{prefix}, {answer}", priority=ResponsePriority.STRONG_CONTINUE,
    #                                        needs_prompt=False, state=state, cur_entity=cur_entity,
    #                                        conditional_state=ConditionalState(
    #                                            prev_treelet_str=self.rg.discuss_section_further_treelet.name,
    #                                            next_treelet_str=self.name,
    #                                            cur_doc_title=cur_entity.name))
    #     else:
    #         return ResponseGeneratorResult(text=f"Sorry, I'm not too sure myself. Do you still want to talk about "
    #                                             f"{cur_entity.talkable_name}?",
    #                                        priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False, state=state,
    #                                        cur_entity=cur_entity, conditional_state=ConditionalState(
    #                                             prev_treelet_str=self.name,
    #                                             next_treelet_str='transition',
    #                                             cur_doc_title=cur_entity.name)
    #                                        )

    def _remove_used_sentences(self, summary, prev_summary):
        """
        Remove sentences from the summary that were used in the previous summary
        :param summary:
        :param prev_summary:
        :return:
        """
        prev_sents = self.rg.get_sentence_segments(prev_summary)
        # print(f"Previous summary sents are: {prev_sents}")
        prev_sents = set(prev_sents)
        sents = self.rg.get_sentence_segments(summary)
        # print(f"Current summary sents are: {sents}")
        # prev sentences may incorporate acknowledgements and other tweaks so this more stringent check is necessary
        # to prevent duplicate sentences -- Caleb
        filtered_summary = ' '.join([s for s in sents if all(s not in prev_sent for prev_sent in prev_sents)])
        # print(f"Filtered summary is: {filtered_summary}")
        return filtered_summary

    def get_acknowledgement(self):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if ResponseType.CONFUSED in response_types: return random.choice(ERROR_ADMISSION)

        prefix = ''

        if ResponseType.AGREEMENT in response_types:
            return random.choice(RESPONSES_TO_USER_AGREEMENT)
        if ResponseType.POS_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types:
                prefix = random.choice(POS_OPINION_RESPONSES)
            elif ResponseType.APPRECIATIVE in response_types:
                return random.choice(APPRECIATION_DEFAULT_ACKNOWLEDGEMENTS)
        elif ResponseType.NEG_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types: # negative opinion
                prefix = "That's an interesting take,"
            else: # expression of sadness
                return random.choice(COMMISERATION_ACKNOWLEDGEMENTS)
        elif ResponseType.NEUTRAL_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types or ResponseType.PERSONAL_DISCLOSURE in response_types:
                return random.choice(NEUTRAL_OPINION_SHARING_RESPONSES)
        elif ResponseType.KNOW_MORE:
            return "Yeah,"
        if prefix is not None:
            # return self.get_neural_response(prefix=prefix, allow_questions=False) TODO need prefixed neural gen
            return prefix
        return random.choice(POST_SHARING_ACK)

    def get_entity_group_name(self, cur_entity) -> str:
        # check if entity belongs to a valid entity group
        ent_group_name = None
        for ent_group_name, ent_group in ENTITY_GROUPS_FOR_CLASSIFICATION.ordered_items:
            if ent_group.matches(cur_entity) and ent_group_name in OPEN_QUESTIONS_DICTIONARY and \
                    OPEN_QUESTIONS_DICTIONARY[ent_group_name]:
                return ent_group_name
        return ent_group_name

    def get_open_question(self, cur_entity):
        ent_group_name = self.get_entity_group_name(cur_entity)
        text = None
        if ent_group_name:
            for return_type, questions in OPEN_QUESTIONS_DICTIONARY[ent_group_name].items():
                if questions:
                    open_question = self.choose(questions)
                    logger.primary_info(
                        f'WIKI has an open question {open_question} for {cur_entity.name} matching EntityGroup: "{ent_group_name}"')
                    text = open_question.format(entity=cur_entity.talkable_name)
        if text is None:
            text = self.choose(open_answer_prompts(cur_entity))
        return random.choice(["Anyway, I was wondering, ", "In any case, I was wondering, "]) + text

    def get_initial_acknowledgement(self, section: WikiSection, elab_available: bool):
        """
        :param section:
        :param elab_available:
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        ack = None
        # continuer = "You might also find it interesting that"
        if ResponseType.CONFUSED in response_types or ResponseType.KNOW_MORE in response_types:
            if elab_available:
                if ResponseType.CONFUSED in response_types:
                    ack = "Sorry if that wasn't clear, let me elaborate."
                else:
                    ack = "Well, I also know that"
            else:
                ack = f"Unfortunately, I don't know much else about {section.page_title}'s {section.title}."

        elif ResponseType.DIDNT_KNOW in response_types:
            ack = self.choose(RESPONSE_TO_DIDNT_KNOW)
        elif ResponseType.THATS in response_types:
            ack = self.choose(RESPONSE_TO_THATS)
        elif ResponseType.AGREEMENT in response_types:
            ack = self.choose(RESPONSES_TO_USER_AGREEMENT)
        # elif ResponseType.NO in response_types:
        #     ack = "Oh, I hope I didn't make a mistake in explaining that!"
        elif ResponseType.POS_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types:
                ack = random.choice(POS_OPINION_RESPONSES)
            elif ResponseType.APPRECIATIVE in response_types:
                ack = random.choice(APPRECIATION_DEFAULT_ACKNOWLEDGEMENTS)
        elif ResponseType.NEG_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types: # negative opinion
                ack = "That's an interesting take,"
            else: # expression of sadness
                ack = random.choice(COMMISERATION_ACKNOWLEDGEMENTS)
        elif ResponseType.NEUTRAL_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types or ResponseType.PERSONAL_DISCLOSURE in response_types:
                ack = random.choice(NEUTRAL_OPINION_SHARING_RESPONSES)

        if ack is None:
            ack = get_random_fallback_neural_response(self.get_current_state())
            if ack is None:
                ack = self.choose(POST_SHARING_ACK)
        return ack

    def get_initial_response(self):
        """
        Response on the first turn in this treelet
        :return:
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        section = state.discussed_section
        entity = state.cur_entity
        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str=self.name,
                                             cur_doc_title=entity.name)

        if ResponseType.NO in response_types:
            # exit immediately
            return self.rg.handle_rejection_response(prefix="Oh, I hope I didn't make a mistake in explaining that!")

        # get elaboration on WikiSection ready
        elab = section.summarize(max_words=250, max_sents=6)
        # print(f"Long elab {elab}")
        elab = wiki_utils.check_section_summary(self.rg, elab, section, allow_history_overlap=True)
        elab = self._remove_used_sentences(elab, self.rg.get_previous_bot_utterance())

        ack = self.get_initial_acknowledgement(section, elab_available=elab is not None)
        qn = self.get_open_question(cur_entity=entity)

        response = f"{ack} {elab} {qn}" if elab else f"{ack} {qn}"

        return ResponseGeneratorResult(text=response,
                                       priority=ResponsePriority.STRONG_CONTINUE,
                                       needs_prompt=False, state=state,
                                       cur_entity=entity, conditional_state=conditional_state)

    def get_followup_acknowledgement(self):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if ResponseType.DONT_KNOW in response_types:
            ack = self.choose(RESPONSE_TO_DONT_KNOW)
        elif ResponseType.THATS in response_types:
            ack = self.choose(RESPONSE_TO_THATS)
        elif ResponseType.DIDNT_KNOW in response_types:
            ack = self.choose(RESPONSE_TO_DIDNT_KNOW)
        elif ResponseType.NOTHING in response_types:
            ack = self.choose(RESPONSE_TO_NOTHING_ANS)
        elif ResponseType.BACKCHANNEL in response_types:
            ack = self.choose(RESPONSE_TO_BACK_CHANNELING)
        else:
            ack = get_random_fallback_neural_response(current_state=self.get_current_state())
            if ack is None:
                ack = self.choose(POST_SHARING_ACK)
        return ack

    def get_followup_response(self):
        """
        Response on second turn in this treelet
        :return:

        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        section = state.discussed_section
        entity = state.cur_entity
        qn = random.choice(DISCUSS_FURTHER_QUESTION).format(entity.talkable_name)
        conditional_state = ConditionalState(prev_treelet_str=self.name,
                                             next_treelet_str='transition',
                                             cur_doc_title=entity.name)

        if ResponseType.NO in response_types: # exit immediately
            return self.rg.handle_rejection_response(prefix="Oh, I hope I didn't make a mistake in explaining that!")

        ack = self.get_followup_acknowledgement()

        return ResponseGeneratorResult(text=f"{ack} {qn}",
                                       priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False, state=state,
                                       cur_entity=entity, conditional_state=conditional_state)

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """
        This method will attempt to select a section to talk about given the user's utterance
        which we assume is neither yes or no.
        """
        state, utterance, response_types = self.get_state_utterance_response_types()

        if state.prev_treelet_str == self.rg.discuss_section_treelet.name: # first time in discuss_section_further
            return self.get_initial_response()
        else:
            return self.get_followup_response()
