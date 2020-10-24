import logging
from typing import Optional, Tuple

from chirpy.core.callables import ResponseGenerator
from chirpy.core.response_priority import PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, emptyResult, \
    UpdateEntity, ResponsePriority
from chirpy.response_generators.categories.regex_templates import CategoriesTemplate
from chirpy.response_generators.categories.categories import CATEGORYNAME2CLASS, ACTIVATIONPHRASE2CATEGORYNAME
from chirpy.response_generators.categories.classes import State, ConditionalState
from chirpy.response_generators.categories.treelets.introductory_treelet import IntroductoryTreelet
from chirpy.response_generators.categories.treelets.handle_answer_treelet import HandleAnswerTreelet
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name
from chirpy.core.smooth_handoffs import SmoothHandoff
from chirpy.core.util import contains_phrase

logger = logging.getLogger('chirpylogger')

QUESTION_CONNECTORS = [
    "So ",
    "This is a little random but ",
    "There's actually something else I wanted to ask you about, ",
    "This is unrelated but I was just thinking, ",
    "So, I just thought of something. ",
    "Anyway, um, on another subject. ",
    "Hmm, so, on another topic. ",
    "Oh hey, I just remembered another thing I've been wondering about. ",
    "Anyway, there’s actually an unrelated thing I wanted to know. ",
    "This is a bit random, but I just remembered something I wanted to ask you. "
]

def get_user_initiated_category(user_utterance, current_state) -> Tuple[Optional[str], bool]:
    """
    If the user utterance matches RegexTemplate, return the name of the category they're asking for.
    Otherwise return None.

    Returns:
        category: the category being activated
        posnav: whether the user has posnav
    """
    slots = CategoriesTemplate().execute(user_utterance)

    # Legacy code; not removing in case it breaks something
    if slots is not None and slots["keyword"] in ACTIVATIONPHRASE2CATEGORYNAME:
        category_name = ACTIVATIONPHRASE2CATEGORYNAME[slots['keyword']]
        logger.primary_info(f'Detected categories intent for category_name={category_name} and slots={slots}.')
        return category_name, True

    # If any activation phrase is in the posnav slot, activate with force_start
    nav_intent = getattr(current_state, 'navigational_intent', None)
    if nav_intent and nav_intent.pos_intent and nav_intent.pos_topic_is_supplied:
        pos_topic = nav_intent.pos_topic[0]  # str
        for activation_phrase, category_name in ACTIVATIONPHRASE2CATEGORYNAME.items():
            if contains_phrase(pos_topic, {activation_phrase}, lowercase_text=False, lowercase_phrases=False, remove_punc_text=False, remove_punc_phrases=False):
                logger.primary_info(f"Detected categories activation phrase '{activation_phrase}' in posnav slot, so categories is activating with force_start")
                return category_name, True

    # If any activation phrase is in the user utterance, activate with can_start
    for activation_phrase, category_name in ACTIVATIONPHRASE2CATEGORYNAME.items():
        if contains_phrase(user_utterance, {activation_phrase}, lowercase_text=False, lowercase_phrases=False, remove_punc_text=False, remove_punc_phrases=False):
            logger.primary_info(f"Detected categories activation phrase '{activation_phrase}' in utterance (but not in a posnav slot), so categories is activating with can_start")
            return category_name, False

    return None, False


class CategoriesResponseGenerator(ResponseGenerator):
    name='CATEGORIES'

    # Make a mapping from treelet name (str) to an initialized Treelet
    treeletname2treelet = {treelet_class.__name__: treelet_class() for treelet_class in [IntroductoryTreelet, HandleAnswerTreelet]}

    def init_state(self) -> State:
        return State()

    def get_entity(self, state) -> UpdateEntity:
        return UpdateEntity(False)

    def get_response(self, state: State) -> ResponseGeneratorResult:

        # If the user is requesting a category, set cur_treelet to Introductory with that category. Otherwise run state.cur_treelet
        utterance = self.state_manager.current_state.text.lower()
        user_initiated_category, user_has_posnav = get_user_initiated_category(utterance, self.state_manager.current_state)
        if user_initiated_category is not None:
            state.cur_category_name = user_initiated_category
            logger.primary_info(f'Getting response from {IntroductoryTreelet.__name__}')
            cur_treelet = IntroductoryTreelet.__name__  # str
        else:
            cur_treelet = state.cur_treelet  # str

        # Get response from cur_treelet
        if cur_treelet:
            logger.primary_info(f'Running categories treelet {cur_treelet}')
            response_result = self.treeletname2treelet[cur_treelet].get_response(state, self.state_manager)
            if cur_treelet == 'IntroductoryTreelet' and response_result.priority == ResponsePriority.FORCE_START and not user_has_posnav:
                logger.primary_info("Setting response priority to CAN_START as the user does not have posnav")
                response_result.priority = ResponsePriority.CAN_START
            return response_result
        else:
            return emptyResult(state)


    def get_prompt(self, state: State) -> PromptResult:
        """
        Randomly choose an undiscussed generic category and ask its first question.
        """
        
        # If this is a smooth transition from movies, get a prompt for tv category from the Introductory treelet
        if self.state_manager.current_state.smooth_handoff == SmoothHandoff.MOVIES_TO_CATEGORIES:
            logger.primary_info('Getting prompt from tv IntroductoryTreelet.')
            state.cur_category_name = 'TVCategory'
            question = state.get_first_unasked_question(state.cur_category_name)
            if question is None:
                logger.warning('Unable to complete smooth handoff from movies to categories because we have no unasked tv questions left')
            else:
                new_entity = get_entity_by_wiki_name(question.cur_entity_wiki_name, self.state_manager.current_state)
                conditional_state = ConditionalState(HandleAnswerTreelet.__name__, state.cur_category_name, None, question.question, False)
                result = PromptResult(question.question, PromptType.FORCE_START, state, cur_entity=new_entity,
                                      expected_type=question.expected_type, conditional_state=conditional_state)
                return result
        
        # If the user is requesting a category, get a prompt for that category from the Introductory treelet
        utterance = self.state_manager.current_state.text.lower()
        user_initiated_category, user_has_posnav = get_user_initiated_category(utterance, self.state_manager.current_state)
        if user_initiated_category is not None:
            state.cur_category_name = user_initiated_category
            logger.primary_info(f'Getting prompt from {IntroductoryTreelet.__name__}')
            prompt_result = self.treeletname2treelet[IntroductoryTreelet.__name__].get_prompt(state, self.state_manager)
            if prompt_result.text is not None and not user_has_posnav:
                logger.primary_info("Setting prompt type to CONTEXTUAL as the user does not have posnav")
                prompt_result.type = PromptType.CONTEXTUAL
            if prompt_result:
                return prompt_result

        # Ask any remaining unasked generic category questions
        category_name, question = state.get_random_generic_undiscussed_category_question()
        if category_name and question:
            logger.primary_info(f"Randomly chose an undiscussed generic category {category_name}. Asking its first question as a generic prompt.")
            new_entity = get_entity_by_wiki_name(question.cur_entity_wiki_name, self.state_manager.current_state)
            conditional_state = ConditionalState(HandleAnswerTreelet.__name__, category_name, None, question.question, False)
            transition = self.state_manager.current_state.choose_least_repetitive(QUESTION_CONNECTORS)
            result = PromptResult(transition + question.question, PromptType.GENERIC, state, cur_entity=new_entity,
                                  expected_type=question.expected_type, conditional_state=conditional_state)

            return result

        # Otherwise return nothing
        return emptyPrompt(state)

    def update_state_if_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        assert conditional_state is not None, "conditional_state should not be None if response/prompt was chosen"
        state.update(conditional_state)
        return state

    def update_state_if_not_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        # If categories RG is not currently active, reset cur_treelet and cur_category_name
        state.cur_treelet = None
        state.cur_category_name = None
        state.just_asked = False
        return state
