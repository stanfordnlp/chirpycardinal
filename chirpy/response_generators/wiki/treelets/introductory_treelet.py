import random
import logging
from typing import Optional

from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.latency import measure
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.response_generators.wiki.treelets.abstract_treelet import Treelet
import chirpy.response_generators.wiki.wiki_utils as wiki_utils
from chirpy.response_generators.wiki.dtypes import State, CantContinueResponseError, CantRespondError, ConditionalState, \
    CantPromptError

logger = logging.getLogger('chirpylogger')

HAVE_YOU_HEARD_PROMPT = [
    "Have you heard of {}?",
    "Do you know about {}?",
    "Do you know of {}?",
]
PROMPT = "Would you like to learn more about {}?"
PROMPT2 = "Would you like to learn more about either {} or {}?"
PROMPT3  = "Would you like to learn more about either {}, {}, or {}?"

PRIMARY_QUESTION_WORD = [
    "who",
    "who",
    "who's",
    "where",
    "were",
    "where's",
    "what",
    "what's",
    "whats",
    "why",
    "why's",
    "when",
    "when's",
    "which",
    "whose",
    "how",
]


class QuestionTemplate(RegexTemplate):
    slots = {
        'primary_q_word': PRIMARY_QUESTION_WORD,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{primary_q_word}" + NONEMPTY_TEXT,
    ]
    positive_examples = [
        ("i don't know who he is", {'primary_q_word': 'who'}),
        ("what is fiscal deficit", {'primary_q_word': 'what'}),
        ("who is Malia", {'primary_q_word': 'who'}),
        ("what is hansel and gratel", {'primary_q_word': 'what'}),
    ]
    negative_examples = [
        'tell me about britain',
        'don\'t tell me why',
        'what',
    ]

question_template = QuestionTemplate()

class IntroductoryTreelet(Treelet):
    """This treelet gets invoked when we believe that we have entered
    inside a document from some sequence of utterances, and we are about
    to give the user an overview of the section

    Fixme: Probably meant overview of the article

    :param Treelet: The abstract Treelet class
    :type Treelet: Treelet
    """

    def __repr__(self):
        return "Introductory Treelet (WIKI)"

    def __name__(self):
        return "introductory"


    def is_appropriate(self, utterance:str, entity: WikiEntity, previous_bot_response: Optional[str]=None):
        #Fixme: add logging and comments
        POPULARITY_PAGE_VIEW_THRESHOLD = 20000
        if question_template.execute(utterance) and entity.common_name.lower() in utterance:
            return True, f"User probably asked a question about {entity.name}, marking Introductory treelet as appropriate for overview"
        if previous_bot_response and question_template.execute(previous_bot_response.lower()):
            return False, "Previous bot response asked a question, marking Introductory treelet as inappropriate for overview"
        if entity.pageview < POPULARITY_PAGE_VIEW_THRESHOLD:
            return True,"User mentioned a rare entity, marking Introductory treelet as appropriate for overview"

        return False, "No criteria for entity overview appropriateness was satisfied"

    def get_overview(self, entity: str) -> Optional[str]:
        """This method attempts to get a summary of a section. In the future this could be a real
        summarization module

        :param entity: the current resolved WIKI entity
        :type entity: str
        :return: The summary of the section. Currently LEAD-3
        :rtype: str

        >>> treelet = Treelet(None)
        >>> treelet.get_overview('Taylor Swift')
        'Taylor Alison Swift (born December 13, 1989) is an American singer-songwriter.  She is known for narrative songs about her personal life, which have received widespread media coverage.'
        """
        logger.debug(f'Getting overview for: {entity}')
        overview = wiki_utils.overview_entity(entity, self.get_sentseg_fn())
        if not overview:
            logger.info("No overview found")
            return None
        overlapping_bot_utterance = self.rg.has_overlap_with_history(overview, threshold=0.75)
        if overlapping_bot_utterance:
            logger.info(
                f'Overview section has high token level overlap with previous response {overlapping_bot_utterance}')
            return None
        else:
            return overview


    def continue_response(self, base_response_result: ResponseGeneratorResult, new_entity=None) -> ResponseGeneratorResult:
        #Fixme: If in future we want to change entities, do it here
        raise CantContinueResponseError(f"Continue response not defined for {self.__repr__()}")


    @measure
    def get_can_start_response(self, state : State) -> ResponseGeneratorResult:
        """This method returns the response if we are currently at this treelet.
        :type state: chirpy.response_generators.wiki.dtypes.State
        :return: the result of the current turn
        :rtype: ResponseGeneratorResult
        state = state.get_reset_state()
        """

        entity = self.rg.get_recommended_entity(state)
        utterance = self.rg.state_manager.current_state.text
        history = self.rg.state_manager.current_state.history
        previous_bot_response = history[-1] if len(history)>0 else None
        # No good high precision spans to talk about
        if not entity:
            raise CantRespondError("No recommended entity")

        appropriate, reason = self.is_appropriate(utterance=utterance, entity=entity, previous_bot_response=previous_bot_response)
        if not appropriate:
            raise CantRespondError(reason)

        logger.info(f"{entity.name} appropriate for overview because {reason}")
        overview = self.get_overview(entity.name)
        if not overview:
            raise CantRespondError(f"No unused overview found for entity {entity.name}")

        logger.primary_info(f'Wiki has found an overview section for {entity}')
        # If we have an overview, read it
        text = overview
        cur_doc_title = entity.name
        conditional_state = ConditionalState(
            cur_doc_title=cur_doc_title,
            responding_treelet = self.__repr__()
        )
        base_response_result = ResponseGeneratorResult(text=text, priority=ResponsePriority.CAN_START,
                                                       needs_prompt=True, state=state, cur_entity=entity,
                                                       conditional_state=conditional_state)
        return base_response_result

    @measure
    def handle_prompt(self, state: State) -> ResponseGeneratorResult:
        """This method returns the response if we are currently at this treelet.
        :type state: chirpy.response_generators.wiki.dtypes.State
        :return: the result of the current turn
        :rtype: ResponseGeneratorResult
        state = state.get_reset_state()
        """

        utterance = self.rg.state_manager.current_state.text
        entity = self.rg.get_recommended_entity(state)
        if not entity:
            raise CantRespondError("No recommended entity")
        if not self.is_no(utterance):
            raise CantRespondError("The user didn't say no to HAVE_YOU_HEARD style prompt")

        base_response = self.get_can_start_response(state)
        base_response.priority = ResponsePriority.STRONG_CONTINUE
        return base_response

    @measure
    def get_prompt(self, state : State) -> PromptResult:
        """This method prompts the user to either continue to discuss something or disambiguate

        :param state: the current state
        :type state: chirpy.response_generators.wiki.dtypes.State
        :return: the prompt result for the user
        :rtype: PromptResult
        """

        # I'm unsure if this is ever going to be useful, so it'll likely not be called from the
        # from the rg's get prompt function.
        entity = self.rg.get_recommended_entity(state)
        if not entity:
            raise CantPromptError("No recommended entity")
        text = random.choice(HAVE_YOU_HEARD_PROMPT).format(entity.name)
        conditional_state = ConditionalState(
            cur_doc_title=entity.name,
            prompt_handler=self.__repr__(),
        )
        return PromptResult(text=text, prompt_type=PromptType.CONTEXTUAL, state=state, cur_entity=entity,
                            conditional_state=conditional_state)
