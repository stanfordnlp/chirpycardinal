import itertools
import random
import logging
from dataclasses import dataclass

from typing import List, Optional

from chirpy.annotators.convpara import ConvPara
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.latency import measure
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID, OPTIONAL_TEXT_POST, \
    OPTIONAL_TEXT_PRE_GREEDY
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.util import filter_and_log, contains_phrase, get_ngrams
from chirpy.response_generators.wiki.dtypes import State, CantRespondError, ConditionalState
from chirpy.response_generators.wiki.treelets.abstract_treelet import HANDOVER_TEXTS, CONVPARA_BLACKLISTED_ENTITIES
from chirpy.response_generators.wiki.treelets.til_treelet import TILTreelet, I_LEARNED, ACKNOWLEDGE_NO


UNABLE_TO_ANSWER = ["Sorry, I don't have an answer for that.", "I don't know actually."]

logger = logging.getLogger('chirpylogger')

HIGH_PREC_QUESTION_WORD = [ "who", "who's", "where", "were", "where's", "what", "what's", "whats", "why", "why's", "when",
                  "when's", "which", "whose", "how"]
QUESTION_WORD = [ "who", "who's", "where", "were", "where's", "what", "what's", "whats", "why", "why's", "when",
    "when's", "which", "whose", "how", "is", "did", "was", "can"]
CONVERSATIONAL_MARKER = [ "talk", "say", "talking", "saying", "understand", "clarify", "mean", "said", "meant"]

def original_til_templates(apologize:bool, original_til: str):
    APOLOGIZE_THEN_ORIGINAL = \
        ["Sometimes I get things wrong. ",
         "Every so often I have trouble understanding what I read. ",
         "Let's see if I can read it again more clearly this time. ",
         "Oh, sorry, maybe I misremembered the details. " ,
         "Ah, sorry, maybe I said it wrong. "]
    THEN_ORIGINAL = [
        f"I'll quote the source. I read on wikipedia that {original_til}.",
        f"Going back to the original version, it said {original_til}.",
        f"What I saw on Wikipedia was that {original_til}.",
        f"Let's see, I think the original version was that {original_til}.",
        F"I remember the original version on Wikipedia saying that {original_til}."
    ]

    if apologize:
        return [a+b for (a, b) in zip(APOLOGIZE_THEN_ORIGINAL, THEN_ORIGINAL)]
    else:
        return THEN_ORIGINAL

def deflect_questions_with_original_til_templates(original_til: str):
    DEFLECT_WITH_ORIGINAL = [
        f"I don't know all the details. What I read on wikipedia that {original_til}.",
        f"I'm not sure, all that I saw on Wikipedia was that {original_til}.",
        f"Not entirely sure. All that I remember was that {original_til}.",
        f"I'm not sure I know exactly. I just remember that {original_til}."
    ]
    return DEFLECT_WITH_ORIGINAL

class DidYouKnowQuestionTempalate(RegexTemplate):
    def execute(self, input_string:str):
        return super().execute(input_string.lower())

    slots = {
        'q_word': ['did', 'do', 'have'],
        'verb': ['know', 'learn', 'heard', 'like', 'try', 'tried', 'hear', 'love', 'loved'],
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{q_word} you (ever )?{verb}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ("Oh yeah, yeah, I'll have to check those out. Have you heard about Google's geospatial data visualization company? It's called keyhole, and it's used in google Earth!".lower(),
         {'q_word': 'have', 'verb': 'heard'}),

        ("I love Hawaii and have been to Hawaii! Do you know about that island where they united by the great king Kamehameha?".lower(),
         {'q_word': 'do', 'verb': 'know'}),
        ("Have you ever tried Blue, the banana?",
         {'q_word': 'have', 'verb': 'tried'})
    ]
    negative_examples = [
        "i guess he suffers from a form of the depression that has happened with people before"
        "I heard that Anton Salonen caused an international incident after his Finnish father, with the help of Finnish diplomats, kidnapped his son back after the boys Russian mother kidnapped the boy in the first place. I wonder if he's a Finnish citizen?",
    ]
did_you_know = DidYouKnowQuestionTempalate()
class ClarificationQuestionTemplate(RegexTemplate):
    slots = {
        'q_word': QUESTION_WORD,
        'hq_word': HIGH_PREC_QUESTION_WORD,
        'conversational_marker': CONVERSATIONAL_MARKER,
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{q_word}" + OPTIONAL_TEXT_MID + "{conversational_marker}" + OPTIONAL_TEXT_POST,
        "{q_word}",
        ]
    positive_examples = [
        ('what are you talking about', {'q_word': 'what', 'conversational_marker': 'talking'}),
        ('what do you mean', {'q_word': 'what', 'conversational_marker': 'mean'}),
        ('can you please clarify', {'q_word': 'can', 'conversational_marker': 'clarify'}),
        ('that is wrong what are you saying', {'q_word': 'what', 'conversational_marker': 'saying'}),
    ]
    negative_examples = [
        "i don't understand",
        "that doesn't make sense",
    ]

class QuestionTemplate(RegexTemplate):
    slots = {
        'q_word': HIGH_PREC_QUESTION_WORD,
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{q_word}" + OPTIONAL_TEXT_POST,
        ]
    positive_examples = [
        ('what are you talking about', {'q_word': 'what'}),
        ('who was it', {'q_word': 'who'})
    ]
    negative_examples = [
        "i don't understand",
        "that doesn't make sense",
    ]
NEGATIVE_WORDS = ['not', "doesn't", "isn't", "hasn't", "won't", "don't", "didn't", 'no']
CORRECTNESS_MARKER = ["correct", "right", "clear", "good", 'sense', 'smart', 'understand', 'sure', 'true']
INCORRECTNESS_MARKER = ["incorrect", "wrong", "unclear", 'nonsense', 'nonsensical', 'stupid', 'unsure', 'untrue']
class DoubtfulTemplate(RegexTemplate):
    slots = {
        'negative_word': NEGATIVE_WORDS,
        'correctness_marker': CORRECTNESS_MARKER,
        'incorrectness_marker': INCORRECTNESS_MARKER
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{negative_word}" + OPTIONAL_TEXT_MID + "{correctness_marker}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE_GREEDY + "{incorrectness_marker}" + OPTIONAL_TEXT_POST,
        'no', 'what'
        ]
    positive_examples = [
        ("that doesn't sound right", {'negative_word': "doesn't", 'correctness_marker': 'right'}),
        ("that's wrong", {'incorrectness_marker': 'wrong'}),
        ("that's stupid", {'incorrectness_marker': 'stupid'}),
        ("i don't understand", {'negative_word': "don't", 'correctness_marker': 'understand'}),
        ('no makes sense', {'negative_word': 'no', 'correctness_marker': 'sense'}),
        ('i\'m not sure about it', {'negative_word': 'not', 'correctness_marker': 'sure'})
    ]
    negative_examples = [
        'what do you mean',
    ]

POSITIVE_WORDS = ['wow', 'interesting', 'surprising', 'cool', 'awesome', 'think', 'wonder', 'ha', 'haha', 'like', 'love', 'funny', 'heard']
class PositiveResponseTemplate(RegexTemplate):
    slots = {
        'positive_word': POSITIVE_WORDS,
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{positive_word}" + OPTIONAL_TEXT_POST,
        ]
    positive_examples = [
        ("wow, that's so cool", {'positive_word': 'cool'}),
        ('that is interesting', {'positive_word': 'interesting'}),
        ('i like it', {'positive_word': 'like'}),
    ]
    negative_examples = [
        "that is so hamburger",
    ]

NEGATIVE_WORDS = ['boring', 'else', 'move on', 'ask', 'stupid', 'bad', 'dumb']
class NegativeResponseTemplate(RegexTemplate):
    slots = {
        'negative_word': NEGATIVE_WORDS,
    }
    templates = [
        OPTIONAL_TEXT_PRE_GREEDY + "{negative_word}" + OPTIONAL_TEXT_POST,
        ]
    positive_examples = [
        ("that was boring", {'negative_word': 'boring'}),
        ("you are stupid", {'negative_word': 'stupid'}),
        ("that was in such a bad taste", {'negative_word': 'bad'}),
    ]
    negative_examples = [
        "that is so hamburger",
        "what do you mean",
        "i don't understand"
    ]

doubtful = DoubtfulTemplate()
clarify = ClarificationQuestionTemplate()
interested = PositiveResponseTemplate()
disinterested = NegativeResponseTemplate()

bigram_overlap_for_repeating_threshold = 0.8
@dataclass
class ConvParaPreferences:
    """Preferances for ranking conversational paraphrases. Higher ranked variables are higher priority"""
    higher_unigram_recall:bool = None
    statement_or_question:str = None #statement or question or none

class ConvParaTILTreelet(TILTreelet):
    """
    This treelet takes some fact (TIL) and uses a conversationally paraphrased version
    """
    def __repr__(self):
        return "ConvPara TIL Treelet (WIKI)"

    def respond_til(self, state: State, entity: WikiEntity, preferences: Optional[ConvParaPreferences] = None, til_text=False) -> ResponseGeneratorResult:
        if entity.name in CONVPARA_BLACKLISTED_ENTITIES:
            raise CantRespondError(f"{entity} blacklisted for convpara")
        if not til_text:
            til_response = self.get_til(entity.name, state)
            if not til_response:
                raise CantRespondError("Not responding with more TILs")
            til_text, _, _ = til_response

        paraphrases = ConvPara(self.rg.state_manager).get_paraphrases(background=til_text,
                                                                                            entity=entity.name)
        paraphrases = filter_and_log(lambda p: p.finished, paraphrases, "Paraphrases for TIL", "they were unfinished")
        paraphrases = filter_and_log(lambda p: not contains_offensive(p.readable_text()), paraphrases, "Paraphrases for TIL", "contained offensive phrase")
        if not paraphrases:
            raise CantRespondError(f"No good conv paraphrases for TIL \n {til_text}")
        if preferences:
            if preferences.statement_or_question:
                if preferences.statement_or_question == 'question':
                    paraphrases = sorted(paraphrases,
                                     key=lambda p: did_you_know.execute(p.readable_text()), reverse=True)
                else:
                    paraphrases = sorted(paraphrases,
                                         key=lambda p: not did_you_know.execute(p.readable_text()), reverse=True)
            if preferences.higher_unigram_recall:
                generations_for_other_tils = state.entity_state[entity.name].conv_paraphrases[til_text] if til_text in state.entity_state[entity.name].conv_paraphrases else []
                paraphrases = sorted(paraphrases, key=lambda p: self.ngram_recall([p.readable_text()] + generations_for_other_tils, til_text, 1), reverse=True)
            text = paraphrases[0].readable_text()
        else:
            text = random.choice([p.readable_text() for p in paraphrases])
        if text[-1] not in ['.', '!', '?']:
            text+='.'

        logger.primary_info(f'WIKI is responding with a *paraphrased* TIL to entity {entity.name}')
        logger.primary_info(f"TIL text: {til_text} \n ConvPara output: {text}")
        conditional_state = ConditionalState(
            cur_doc_title=entity.name,
            til_used=til_text,
            responding_treelet=self.__repr__(),
            prompt_handler=f"{self.__repr__()}:paraphrase_handler",
            paraphrase=(til_text, text))
        base_response_result = ResponseGeneratorResult(
            text=text,
            priority=ResponsePriority.CAN_START,
            cur_entity=entity,
            needs_prompt=False,
            state=state,
            conditional_state=conditional_state)
        return base_response_result

    @measure
    def get_can_start_response(self, state : State) -> ResponseGeneratorResult:
        """This method returns a TIL if we have one and then disambiguate,
        or we delegate to our super class to handle the rest

        :param state: The current state of the RG
        :type state: chirpy.response_generators.wiki.dtypes.State
        :return: the result which we use to utter
        :rtype: ResponseGeneratorResult

        """
        utterance = self.rg.state_manager.current_state.text.lower()
        entity = self.rg.get_recommended_entity(state)
        if not entity:
            raise CantRespondError("No recommended entity")
        base_response =  self.respond_til(state, entity, preferences=ConvParaPreferences(higher_unigram_recall=True))
        base_response.cur_entity = entity
        return base_response


    @measure
    def get_prompt(self, state: State) -> PromptResult:
        prompt_result = super().get_prompt(state)
        prompt_result.conditional_state.prompt_handler = f"{self.__repr__()}:wanna_know_more"
        return prompt_result

    @measure
    def continue_response(self, base_response_result: ResponseGeneratorResult) -> ResponseGeneratorResult:
        response_result = super().continue_response(base_response_result)
        response_result.conditional_state.prompt_handler = f"{self.__repr__()}:wanna_know_more"
        return response_result

    @measure
    def handle_prompt(self, state: State) -> ResponseGeneratorResult:
        utterance = self.rg.state_manager.current_state.text.lower()
        last_entity = self.rg.state_manager.current_state.entity_tracker.last_turn_end_entity
        entity = self.rg.get_recommended_entity(state)
        if entity != last_entity:
            raise CantRespondError("Recommended entity changed from last turn")
        is_question = self.rg.state_manager.current_state.question['is_question']

        # Prompt came from this (i.e. TIL treelet's) get_prompt function, which has a yes/no answer.
        prompt_subhandler = state.prompt_handler.split(':')[1]
        if prompt_subhandler == 'wanna_know_more':
            # We should continue only for yes
            if self.is_yes(utterance) and entity:
                first_til_response = self.get_can_start_response(state)
                first_til_response.priority = ResponsePriority.STRONG_CONTINUE
                return first_til_response

            elif self.is_no(utterance):
                return ResponseGeneratorResult(text=random.choice(ACKNOWLEDGE_NO),
                                               priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                               state=state,
                                               cur_entity=None, conditional_state=ConditionalState(
                        responding_treelet=self.__repr__(),

                    ))

            raise CantRespondError("couldn't classify user response into YES or NO")


        # Else : need to gauge engagement based on user response
        elif prompt_subhandler == 'paraphrase_handler':
            last_til = state.entity_state[entity.name].tils_used[-1]
            generations_for_last_til = state.entity_state[entity.name].conv_paraphrases[last_til]
            last_utterance_was_did_you_know_question = did_you_know.execute(generations_for_last_til[-1]) if len(generations_for_last_til)>0 else False

            unigram_overlap = self.ngram_recall(generations_for_last_til, last_til, 2)
            bigram_overlap = self.ngram_recall(generations_for_last_til, last_til, 2)
            bigram_unigram_overlap = (unigram_overlap + bigram_overlap) /2
            content_not_covered = bigram_unigram_overlap < bigram_overlap_for_repeating_threshold

            logger.primary_info(f"Last utterance has {unigram_overlap} unigram_overlap and {bigram_unigram_overlap} average unigram-bigram overlap with the TIL it paraphrased")
            # Cases:
            # User asks for clarification, is confused, or didn't understand what we said
            # These regexes are high precision and if the user is confused or unclear it probably means we paraphrased
            # incorrectly
            if (clarify.execute(utterance) or doubtful.execute(utterance)):
                # Apologize and read out the original til
                text = self.rg.state_manager.current_state.choose_least_repetitive(original_til_templates(apologize=True, original_til=last_til))
                conditional_state = ConditionalState(
                    cur_doc_title=entity.name,
                    responding_treelet=self.__repr__(),
                    til_used=last_til)
                state.convpara_measurement['codepath'] = 'apologize_with_original_phrasing_for_unclear_paraphrase'
                response_result = ResponseGeneratorResult(text=text, priority=ResponsePriority.STRONG_CONTINUE,
                                                               needs_prompt=True, state=state, cur_entity=entity,
                                                               conditional_state=conditional_state)

                logger.primary_info(f'WIKI is responding with an apology and a non-paraphrased version of the previous TIL entity {entity}')
                return response_result

            # If user sounds disinterested
            elif disinterested.execute(utterance):
                # Do not generate another TIL response
                logger.primary_info("ConvPara TIL detected explicitly disinterested user. Handing over with WEAK_CONTINUE")
                apology_text = random.choice(HANDOVER_TEXTS)
                apology_response = ResponseGeneratorResult(
                    text=apology_text,
                    priority=ResponsePriority.WEAK_CONTINUE,
                    needs_prompt=True,
                    cur_entity=None,
                    state=state,
                    conditional_state=ConditionalState(
                        responding_treelet=self.__repr__(),
                    )
                )
                apology_response.state.convpara_measurement['codepath']='apology_handover_for_explicitly_disinterested'

                return apology_response

            elif (not last_utterance_was_did_you_know_question) and utterance == 'no':
                # Read out the original til without apologizing
                # Rationale is that users often say no because they are surprised, and we can read out the til verbatim
                # There's a chance we said it wrong the first time, but typically in that case clarify or doubtful catch it
                text = self.rg.state_manager.current_state.choose_least_repetitive(original_til_templates(apologize=False, original_til=last_til))
                conditional_state = ConditionalState(
                    cur_doc_title=entity.name,
                    responding_treelet=self.__repr__(),
                    til_used=last_til)
                state.convpara_measurement['codepath'] = 'original_phrasing_for_no_to_nonquestion_paraphrase'
                response_result = ResponseGeneratorResult(text=text, priority=ResponsePriority.STRONG_CONTINUE,
                                                          needs_prompt=True, state=state, cur_entity=entity,
                                                          conditional_state=conditional_state)

                logger.primary_info(f'User said no to a non-question, WIKI is responding with a non-paraphrased version of the previous TIL entity {entity}')
                return response_result

            elif last_utterance_was_did_you_know_question and unigram_overlap < 0.35 and len(generations_for_last_til)<=1:
                # If we asked a did you know style question in the last paraphrase and didn't talk about much of the til
                # measured using unigram overlap, try paraphrasing but only once

                logger.primary_info(f'WIKI trying the previous TIL with paraphrasing for one more turn '
                                    f'because we asked a did you know kind of question and we didn\'t cover enough content')
                paraphrased_repeat_result = self.respond_til(state, entity, preferences=ConvParaPreferences(higher_unigram_recall=True, statement_or_question='statement'), til_text=last_til)
                paraphrased_repeat_result.priority = ResponsePriority.STRONG_CONTINUE
                paraphrased_repeat_result.state.convpara_measurement['codepath'] = 'paraphrase_for_answer_to_did_you_know'
                return paraphrased_repeat_result

            # User asks a question and all the content is not covered
            # note that just single word questions are covered as part of doubtful or clarification already
            #elif (is_question or contains_phrase(utterance, set(HIGH_PREC_QUESTION_WORD))) and len(generations_for_last_til)<=1:
            #    # We should cite the original TIL and say that's all I know about it
            #    text = self.rg.state_manager.current_state.choose_least_repetitive(deflect_questions_with_original_til_templates(original_til=last_til))
            #    conditional_state = ConditionalState(
            #        cur_doc_title=entity.name,
            #        responding_treelet=self.__repr__(),
            #        til_used=last_til)
            #    state.convpara_measurement['codepath'] = 'deflect_question_with_original_phrasing'
            #    response_result = ResponseGeneratorResult(text=text, priority=ResponsePriority.STRONG_CONTINUE,
            #                                              needs_prompt=True, state=state, cur_entity=entity,
            #                                              conditional_state=conditional_state)
            #    logger.primary_info(
            #        "ConvPara TIL deflected question with original phrasing. Handing over with WEAK_CONTINUE")
            #    return response_result


            # If user sounds interested
            elif interested.execute(utterance):
                # Generate response using paraphrasing
                base_response = self.respond_til(state, entity, preferences=ConvParaPreferences(higher_unigram_recall=True))
                base_response.cur_entity = entity
                base_response.priority = ResponsePriority.STRONG_CONTINUE
                base_response.state.convpara_measurement['codepath']='new_convpara_TIL_for_interested_user'
                return base_response

        # Fixme: store user satisfaction for convpara til
        state.convpara_measurement['codepath'] = 'disinterested'
        raise CantRespondError("User wasn't very interested, not using convpara til anymore")

