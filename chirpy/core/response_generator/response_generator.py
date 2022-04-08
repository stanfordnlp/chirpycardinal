from chirpy.core.callables import NamedCallable
from chirpy.core.state_manager import StateManager
from chirpy.core.regex import response_lists
from chirpy.core.response_generator.response_type import *
from chirpy.core.response_generator.neural_helpers import is_two_part, NEURAL_DECODE_CONFIG, get_random_fallback_neural_response
from chirpy.core.response_generator.state import NO_UPDATE, BaseState, BaseConditionalState
from chirpy.core.response_generator.neural_helpers import get_neural_fallback_handoff, neural_response_filtering
from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyResult, \
    emptyResult_with_conditional_state, emptyPrompt, UpdateEntity, AnswerType
from chirpy.core.response_generator.helpers import *
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.util import load_text_file
from typing import Set, Optional, List, Dict
import logging

from chirpy.annotators.blenderbot import BlenderBot
from chirpy.annotators.sentseg import NLTKSentenceSegmenter
from chirpy.annotators.navigational_intent.navigational_intent import NavigationalIntentOutput

from chirpy.response_generators.acknowledgment.acknowledgment_helpers import ACKNOWLEDGMENT_DICTIONARY
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION

from chirpy.response_generators.music.utils import WikiEntityInterface

from concurrent import futures

logger = logging.getLogger('chirpylogger')

import os
STOPWORDS_FILEPATH = os.path.join(os.path.dirname(__file__), '../../data/long_stopwords.txt')
STOPWORDS = load_text_file(STOPWORDS_FILEPATH)

class ResponseGenerator(NamedCallable):
    def __init__(self,
                 state_manager: StateManager,
                 treelets: Dict[str, Treelet]=None,
                 trigger_words: List[str] = None,
                 intent_templates=None,
                 transition_matrix=None,
                 disallow_start_from=None,
                 can_give_prompts=False,
                 state_constructor=None,
                 conditional_state_constructor=None
                 ):
        """Creates a new Response Generator.

            name: str                                   (e.g. "MUSIC")
            treelets: Dict[str, Treelet]                (a dict from string to Treelet)
            trigger_terms: List[str]                    (a list of strings that activate the RG)
            intent_template: list of class names        (a template to be executed)
        """

        self.state_manager = state_manager
        self.treelets = treelets if treelets else {}
        self.trigger_words = trigger_words if trigger_words else []
        self.can_give_prompts = can_give_prompts
        self.intent_templates = intent_templates if intent_templates else []
        self.transition_matrix = transition_matrix if transition_matrix else {}
        self.disallow_start_from: List[str] = disallow_start_from if disallow_start_from else []
        self.State = state_constructor if state_constructor else BaseState
        self.ConditionalState = conditional_state_constructor if conditional_state_constructor else BaseConditionalState

        # These will be set later
        self._response_types = set()
        self.state = None

    def identify_response_types(self, utterance) -> Set[ResponseType]:
        """
        Returns the set of response types that characterize the user utterance
        :param utterance:
        :return:
        """
        return identify_base_response_types(self, utterance)

    def init_state(self) -> BaseState:
        return self.State()

    def update_state_if_chosen(self, state, conditional_state):
        """
        This method updates the internal state of the response generator,
        given that this RG is chosen as the next turn by the bot dialog manager. This state is accessible given
        the global state of the bot in the variable

        global_state['response_generator_states'][self.name]

        If the attribute value is NO_UPDATE: no update is done for that attribute.
        Otherwise, the attribute value is updated.
        If conditional_state is None: make no update other than saving the response types
        """
        response_types = self.get_cache(f'{self.name}_response_types')
        logger.info(f"Got cache for {self.name} response_types: {response_types}")
        if response_types is not None:
            state.response_types = construct_response_types_tuple(response_types)

        if conditional_state is None: return state

        if conditional_state:
            for attr in dir(conditional_state):
                if not callable(getattr(conditional_state, attr)) and not attr.startswith("__"):
                    val = getattr(conditional_state, attr)
                    if val != NO_UPDATE: setattr(state, attr, val)
        state.num_turns_in_rg += 1
        return state

    def update_state_if_not_chosen(self, state, conditional_state):
        """
        By default, this sets the prev_treelet_str and next_treelet_str to '' and resets num_turns_in_rg to 0.
        Response types are also saved.
        No other attributes are updated.
        All other attributes in ConditionalState are set to NO-UPDATE
        """
        response_types = self.get_cache(f'{self.name}_response_types')
        if response_types is not None:
            state.response_types = construct_response_types_tuple(response_types)

        state.prev_treelet_str = ''
        state.next_treelet_str = ''
        state.num_turns_in_rg = 0

        return state

    def set_user_attribute(self, attr_name, value):
        setattr(self.state_manager.user_attributes, attr_name, value)

    def get_user_attribute(self, attr_name, default):
        return getattr(self.state_manager.user_attributes, attr_name, default)

    def reset_user_attributes(self):
        self.set_user_attribute('name', None)
        self.set_user_attribute('discussed_aliens', False)
        self.set_user_attribute('started_with_food', False)
        self.set_user_attribute('favorite_sport', None)

    def get_previous_bot_utterance(self) -> Optional[str]:
        if len(self.state_manager.current_state.history) > 0:
            previous_bot_utterance = self.state_manager.current_state.history[-1]
        else:
            previous_bot_utterance = None
        return previous_bot_utterance

    def get_previous_user_utterance(self) -> Optional[str]:
        if len(self.state_manager.current_state.history) > 1:
            previous_user_utterance = self.state_manager.current_state.history[-2]
        else:
            previous_user_utterance = None
        return previous_user_utterance

    def get_conversation_history(self) -> List[str]:
        return self.state_manager.current_state.history

    def get_last_active_rg(self) -> Optional[str]:
        return self.state_manager.last_state_active_rg

    def get_last_response(self):
        return self.state_manager.last_state_response

    def get_answer_type(self):
        last_response = self.get_last_response()
        return last_response.answer_type if last_response is not None else None

    def get_last_prompt_rg(self) -> Optional[str]:
        if self.state_manager.last_state:
            return self.state_manager.last_state.selected_prompt_rg

    def get_current_rg_state(self):
        return self.state_manager.current_state.get_rg_state(self.name)

    def get_top_dialogact(self):
        return self.state_manager.current_state.dialogact['top_1']

    def get_dialogact_probdist(self):
        return self.state_manager.current_state.dialogact['probdist']

    def transform_questions_into_statements(self, responses, scores):
        out = []
        for response, score in zip(responses, scores):
            if '?' in response:
                sentences = [x.strip() for x in response.split('.')]
                first_question_index = min([i for i in range(len(sentences)) if '?' in sentences[i]])
                if first_question_index == 0: continue
                response = '. '.join(sentences[:first_question_index])
            out.append((response, score))
        if len(out) == 0: return [], []
        return zip(*out)

    def get_neural_acknowledgement(self):
        """
        Gets a short neural acknowledgement.
        :return:
        """
        # response = self.get_neural_response(allow_questions=False)
        # # get the first part of the response
        # first_part = response.split('.')[0] + '.'
        # return first_part
        return get_random_fallback_neural_response(current_state=self.get_current_state())
    #
    # def get_gpt2ed_acknowledgement(self):
    #     return ""

    def get_neural_response(self, prefix=None, allow_questions=False, conditions=None) -> Optional[str]:
        """
        Get neurally generated response started with specific prefix
        :param prefix: Prefix
        :param allow_questions: whether to allow questions in the response
        :param conditions: list of funcs that filter for desired response
        :return:
        """
        if conditions is None: conditions = []
        history = self.get_conversation_history() + [self.utterance]
        responses, scores = self.get_all_neural_responses(history, prefix=prefix)
        if not allow_questions:
            responses, scores = self.transform_questions_into_statements(responses, scores)
            responses_scores = [(response, score) for response, score in zip(responses, scores) if '?' not in response]
            if len(responses_scores) == 0:
                logger.info("There are 0 suitable neural responses.")
                return None
            responses, scores = zip(*responses_scores)
        best_response = self.get_best_neural_response(responses, scores, history, conditions=conditions)
        return best_response

    def get_all_neural_responses(self, history, prefix=None):
        """
        Sends history to BlenderBot and returns response.

        Args:
            history: history of utterances in the conversation thus far
            prefix: utterance prefix that the generated utterance should begin with

        Returns:
             response: str, or None in case of error or nothing suitable. Guaranteed to end in a sentence-ending token.
        """
        if prefix:
            # If there's a prefix, we aren't retrieving the prefetched and cached response.
            # We have to run a generation call again.
            bbot = BlenderBot(self.state_manager)
            return bbot.execute(input_data={'history': history}, prefix=prefix)
        if isinstance(self.state_manager.current_state.blenderbot, futures.Future):
            # Sometimes the call to BlenderBot has not yet finished, in which case we store the future
            # in self.state_manager.current_state.blenderbot and retrieve the result here.
            future_result = self.state_manager.current_state.blenderbot.result()
            # Replace the future with the future's result
            setattr(self.state_manager.current_state, 'blenderbot', future_result)
        return self.state_manager.current_state.blenderbot # (responses, scores)

    def get_best_neural_response(self, responses, scores, history, conditions):
        """

        @param responses: list of strings. responses from neural module. Can assume all end in sentence-ending tokens.
        @param history: list of strings. the neural conversation so far (up to and including the most recent user utterance).
        @return: best_response: string, or None if there was nothing suitable.

        """
        num_questions = len([response for response in responses if '?' in response])
        is_majority_questions = num_questions >= len(responses) / 2
        responses, _ = neural_response_filtering(responses, scores)
        responses = [r for r in responses if 'thanks' not in responses]

        for cond in conditions:
            responses = [r for r in responses if cond(r)]

        if len(responses) == 0:
            logger.warning('There are 0 suitable neural responses')
            return None
        responses = sorted(responses,
                           key=lambda response: (  # all these keys should be things where higher is good
                               ('?' in response) if is_majority_questions or len(history)==1 else ('?' not in response),
                                is_two_part(response),
                                len(response),
                           ),
                           reverse=True)
        return responses[0]

    def get_current_entity(self, initiated_this_turn=False):
        """
        :param initiated_this_turn: require that entity was raised by the user this turn
        :return:
        """
        current_state = self.state_manager.current_state
        if initiated_this_turn:
            if current_state.entity_tracker.cur_entity_initiated_by_user_this_turn(current_state):
                return current_state.entity_tracker.cur_entity
            else:
                return None
        else:
            return self.state_manager.current_state.entity_tracker.cur_entity

    def get_entity_tracker(self):
        return self.state_manager.current_state.entity_tracker

    def get_top_entity(self):
        return self.state_manager.current_state.entity_linker.top_ent()

    def is_relevant_entity(self, entity, relevant_categories):
        """

        :param entity:
        :param relevant_categories: List of EntityGroupsForClassification
        :return:
        """
        is_relevant = any([ent_group.matches(entity) for ent_group in relevant_categories])
        return is_relevant

    def get_entity_tracker_history(self):
        return self.state_manager.current_state.entity_tracker.history

    def get_entity_tracker(self):
        return self.state_manager.current_state.entity_tracker

    def get_entities(self):
        return {
            'talked_finished': self.state_manager.current_state.entity_tracker.talked_finished,
            'talked_rejected': self.state_manager.current_state.entity_tracker.talked_rejected,
            'user_mentioned_untalked': self.state_manager.current_state.entity_tracker.user_mentioned_untalked,
            'user_topic_unfound': self.state_manager.current_state.entity_tracker.user_topic_unfound
        }

    def get_navigational_intent_output(self) -> NavigationalIntentOutput:
        return self.state_manager.current_state.navigational_intent

    def get_treelet_for_entity(self, entity):
        entity_treelet_name = None
        for treelet_name, treelet in self.treelets.items():
            for entity_group in treelet.trigger_entity_groups: # TODO generalize WikiEntityInterface
                if WikiEntityInterface.is_in_entity_group(entity, entity_group):
                    if not entity_treelet_name: entity_treelet_name = treelet_name
        return entity_treelet_name

    def get_state_utterance_response_types(self):
        return self.state, self.utterance, self.response_types

    def get_response_types(self):
        return self.response_types

    def emptyResult(self):
        return emptyResult(self.state)

    def emptyPrompt(self):
        return emptyPrompt(self.state)

    def get_entity(self, state) -> UpdateEntity:
        """Updates current topic of conversation"""
        return UpdateEntity(False)

    def emptyResult_with_conditional_state(self, conditional_state=None):
        return emptyResult_with_conditional_state(self.state, conditional_state)

    def get_intro_treelet_response(self) -> Optional[ResponseGeneratorResult]:
        """
        This is called in get_response() when the RG has not been activated yet. This should be overridden by the child
        RG class. A custom check (that is not trigger/entity-related) can be put here to determine if
        the introductory treelet should be activated.

        This method should return None if there is no valid response.

        Note: The 'disallow_start_from' RG list is already checked against before this can be called.
        :return: introductory treelet response
        """
        return None

    def user_has_direct_navigational_intent(self):
        sent_toks = set(self.utterance.split())
        triggered_terms = sent_toks & set(self.trigger_words)
        if len(triggered_terms) > 0:
            for tok in sent_toks:
                if tok in triggered_terms:
                    logger.info(f"{self.name} found a proposed navigational intent: triggered term {tok}")
                    return {"responding_template": "trigger_word", "trigger_word": tok}
        for intent_class in self.intent_templates:
            proposed_intent = intent_class().execute(self.utterance)
            if proposed_intent:
                proposed_intent.update({"responding_template": intent_class.__name__})
                logger.info(f"{self.name} found a proposed navigational intent {proposed_intent}")
                return proposed_intent
        logger.info(f"{self.name} has no strong intent for utterance {self.utterance}.")
        return None

    def handle_user_trigger(self, **kwargs):
        """
            **kwargs: contents of the template that was executed,
            or "word": "contents" if a trigger_word was found.
        """
        for treelet in self.treelets.values():
            logger.info(f"Called get_trigger_response with state={self.state}")
            proposed_response = treelet.get_trigger_response(state=self.state, **kwargs)
            if proposed_response: return proposed_response

    def handle_direct_navigational_intent(self) -> Optional[ResponseGeneratorResult]:
        # Directly starting our conversation
        intro_slots = self.user_has_direct_navigational_intent()
        if intro_slots:
            proposed_response = self.handle_user_trigger(**intro_slots)
            if proposed_response: return proposed_response
        return None

    def _get_priority_from_answer_type(self):
        last_response = self.get_last_response()
        last_answer_type = last_response.answer_type if last_response is not None else None
        entity_should_force_start = (last_answer_type == AnswerType.QUESTION_HANDOFF and (self.get_last_active_rg() != 'NEURAL_CHAT' or self.name == 'FOOD')
                                     or self.get_navigational_intent_output().pos_intent)
        priority = ResponsePriority.FORCE_START if entity_should_force_start else ResponsePriority.CAN_START
        return priority

    def handle_current_entity(self) -> Optional[ResponseGeneratorResult]:
        current_entity = self.get_current_entity(initiated_this_turn=True)
        priority = self._get_priority_from_answer_type()
        if current_entity:
            treelet_name = self.get_treelet_for_entity(current_entity)
            if treelet_name: return self.treelets[treelet_name].get_response(priority)
        return None

    def handle_custom_activation_checks(self) -> Optional[ResponseGeneratorResult]:
        """
        For all the custom triggers that might start the RG
        :return:
        """
        return None

    def handle_change_topic(self):
        """
        Special handler that returns either None (do nothing), a ResponseGeneratorResult (return that result),
        or False (explicitly discontinue the conversation so that non-active RG activation checks can run).

        This hack is necessary for same-RG topic-switches to take place (aka this is the return False case)
        :return:
        """
        return None
        # intro_slots = self.user_has_direct_navigational_intent()
        # if intro_slots:
        #     proposed_response = self.handle_user_trigger(**intro_slots)
        #     if proposed_response: return proposed_response
        # return self.handle_rejection_response(priority=ResponsePriority.WEAK_CONTINUE)

    def handle_exit_response(self) -> Optional[ResponseGeneratorResult]:
        """
        For responses where we want to gently transition from this RG to another RG
        :return:
        """
        text = get_neural_fallback_handoff(self.state_manager.current_state) or "Ok, cool!"
        return ResponseGeneratorResult(text=text, priority=ResponsePriority.WEAK_CONTINUE, needs_prompt=True,
                                       state=self.state, cur_entity=None, conditional_state=self.ConditionalState(),
                                       answer_type=AnswerType.ENDING)

    def handle_question(self) -> Optional[ResponseGeneratorResult]:
        for treelet in self.treelets.values():
            proposed_response = treelet.get_question_response()
            if proposed_response: return proposed_response
        return None
        #     # Attempt to answer question using GPT-2
        # return ResponseGeneratorResult(text=self.get_neural_response())


    def handle_user_clarification(self, slots):
        # check 1-gram overlap -- proxy to see if user is repeating what bot says
        bot_words = self.get_previous_bot_utterance().split()
        non_trivial_overlap_tokens = set(self.utterance.split()) & set(bot_words) - set(STOPWORDS)
        logger.debug(f"Got non-trivial overlap {non_trivial_overlap_tokens} from '{self.utterance.split()}', '{self.get_previous_bot_utterance()}'")

        if any(self.get_previous_bot_utterance().startswith(phrase) for phrase in CONFIRM_SAYING_PHRASES + CORRECT_SAYING_PHRASES + REPETITION_APOLOGY + response_lists.CLARIFICATION_COMPLAINT_RESPONSE):
            # If asked to repeat twice in a row, change topic instead
            return ResponseGeneratorResult(text=f"{self.choose(SORRY_FOR_CONNECTION)}", #..."anyway, I was thinking.... [prompt continues]"
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self.ConditionalState())

        if len(non_trivial_overlap_tokens):
            second_personified_user_query = first_to_second_person(slots.get('query', ''))
            repeated = " ".join([word for word in second_personified_user_query.split() if word in bot_words])
            return ResponseGeneratorResult(text=f"{self.choose(CONFIRM_SAYING_PHRASES)}: {repeated}.", priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self._construct_no_update_conditional_state())
        else:
            last_sentence = get_last_sentence(self.get_previous_bot_utterance())
            return ResponseGeneratorResult(text=f"{self.choose(CORRECT_SAYING_PHRASES)}: {last_sentence}", priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self._construct_no_update_conditional_state())

    def handle_repetition_request(self, slots):
        if any(self.get_previous_bot_utterance().startswith(phrase) for phrase in CONFIRM_SAYING_PHRASES + CORRECT_SAYING_PHRASES + REPETITION_APOLOGY + response_lists.CLARIFICATION_COMPLAINT_RESPONSE):
            # If asked to repeat twice in a row, change topic instead
            return ResponseGeneratorResult(text=f"{self.choose(SORRY_FOR_CONNECTION)}", #..."anyway, I was thinking.... [prompt continues]"
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self.ConditionalState())

        return ResponseGeneratorResult(text=f"{self.choose(REPETITION_APOLOGY)} What I said was, {self.get_previous_bot_utterance()}",
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self._construct_no_update_conditional_state())

    def handle_name_request(self, slots):
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        user_name = getattr(self.state_manager.user_attributes, 'name', None)
        if user_name:
            response = f"If I remember correctly, your name is {user_name}."
        else:
            response = "Hmm, I don't think you gave me your name."
        return ResponseGeneratorResult(text=f"{response} Anyway, as I was saying: {last_sentence}",
                            priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                            state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                            conditional_state=self._construct_no_update_conditional_state())

    def handle_abilities_question(self, slots):
        return ResponseGeneratorResult(text=f"{self.choose(response_lists.HANDLE_ABILITIES_RESPONSE)}",
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self._construct_no_update_conditional_state())

    def handle_personal_question(self, slots):
        continuation = slots.get('action', '')
        if continuation:
            best_response = self.get_neural_response()
            return ResponseGeneratorResult(text=f"{self.choose(THANK_INQUIRY_PHRASES)} {best_response}",
                                        priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=False,
                                        state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                        conditional_state=self._construct_no_update_conditional_state())

    def handle_alexa_command(self, slots):
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        return ResponseGeneratorResult(
            text="This is an Alexa Prize Socialbot. I'm happy to chat with you, but I can't execute typical Alexa "
                    "commands like that one. If you want to stop chatting, just say, stop, and you can "
                    f"try your voice command again. But I'd love to keep talking to you! As I was saying, {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

    def handle_interruption_question(self, slots):
        if self.get_cache(f'{self.name}_last_bot_sentence') is not None: # in the tree. need to decide if user wants to navigate away or if asked a question that requires a neural response.
            back_transition = f"Anyway, as I was saying: {self.get_cache('last_bot_sentence')}"
            self.set_cache(f'{self.name}_last_bot_sentence', None)
            if user_gave_nevermind(self.state_manager.current_state):
                return ResponseGeneratorResult(
                    text=f"Oh, that's okay. {back_transition}",
                    priority=ResponsePriority.STRONG_CONTINUE,
                    needs_prompt=False,
                    state=self.state if self.state is not None else self.State(),
                    cur_entity=self.get_current_entity(),
                    conditional_state=self._construct_no_update_conditional_state()
                    )
            else:
                best_response = self.get_neural_response()
                return ResponseGeneratorResult(
                    text=f"{best_response} {back_transition}",
                    priority=ResponsePriority.STRONG_CONTINUE,
                    needs_prompt=False,
                    state=self.state if self.state is not None else self.State(),
                    cur_entity=self.get_current_entity(),
                    conditional_state=self._construct_no_update_conditional_state()
                    )
        else:
            last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
            self.set_cache(f'{self.name}_last_bot_sentence', last_sentence)
            return ResponseGeneratorResult(
                text="Sure, what's up?",
                priority=ResponsePriority.STRONG_CONTINUE,
                needs_prompt=False,
                state=self.state if self.state is not None else self.State(),
                cur_entity=self.get_current_entity(),
                conditional_state=self._construct_no_update_conditional_state()
                )

    def handle_chatty_phrase(self, slots):
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        logger.primary_info(f"Chatty Phrase: {slots['chatty_phrase']}")
        return ResponseGeneratorResult(
            text=response_lists.ONE_TURN_RESPONSES.get(slots['chatty_phrase'], "Ok, I'd love to talk to you! What would you like to talk about?"),
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

    def handle_user_name_correction(self, slots):
        apology = "Oops, it sounds like I got your name wrong. I'm so sorry about that! I won't make that mistake again."
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        setattr(self.state_manager.user_attributes, 'name', None)
        setattr(self.state_manager.user_attributes, 'discussed_aliens', False)
        return ResponseGeneratorResult(
            text=f"{apology} Anyway, as I was saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

    def handle_story_request(self, slots):
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        return ResponseGeneratorResult(
            text=f"Sure, here's a story someone told me. {self.choose(response_lists.STORIES)}. But anyway, as I was saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

    def handle_compliment(self, slots):
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        return ResponseGeneratorResult(
            text=f"{self.choose(response_lists.COMPLIMENT_RESPONSE)} But anyway, I was just saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

    def handle_age_request(self, slots):
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        return ResponseGeneratorResult(
            text=f"{self.choose(response_lists.HANDLE_AGE_RESPONSE)} But anyway, I was just saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

    def handle_weather(self, slots):
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        return ResponseGeneratorResult(
            text=f"I live in the cloud so I'm not sure what the weather is like on earth! But anyway, I was just saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

    def handle_what_time(self, slots):
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        return ResponseGeneratorResult(
            text=f"I live in the cloud so I'm not sure what time it is on earth! But anyway, I was just saying: {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
            )

    def handle_cutoff_user(self, slots):
        if any(self.get_previous_bot_utterance().startswith(phrase) for phrase in USER_REPEAT_PHRASES):
            # If asked to repeat twice in a row, change topic instead
            return ResponseGeneratorResult(text=f"{self.choose(SORRY_FOR_CONNECTION)}", #..."anyway, I was thinking.... [prompt continues]"
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self.ConditionalState())
        return ResponseGeneratorResult(
            text=self.choose(response_lists.CUTOFF_USER_RESPONSE),
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )

    def handle_misheard_complaint(self, slots):
        cur_ent = self.get_current_entity()
        history = self.state_manager.current_state.entity_tracker.history
        is_initiated_on_last_turn = len(history) >= 2 and cur_ent in history[-2].values()
        if any(self.get_previous_bot_utterance().startswith(phrase) for phrase in USER_REPEAT_PHRASES):
            # If asked to repeat twice in a row, change topic instead
            return ResponseGeneratorResult(text=f"{self.choose(SORRY_FOR_CONNECTION)}", #..."anyway, I was thinking.... [prompt continues]"
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self.ConditionalState())

        return ResponseGeneratorResult(
            text=self.choose(response_lists.MISHEARD_COMPLAINT_RESPONSE),
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=cur_ent if is_initiated_on_last_turn else None,
            conditional_state=self._construct_no_update_conditional_state()
        )

    def handle_unclear_complaint(self, slots):
        last_sentence = get_last_sentence(self.get_previous_bot_utterance(), drop_punctuation=False, split_clauses=True)
        if any(self.get_previous_bot_utterance().startswith(phrase) for phrase in BOT_REPEAT_PHRASES):
            # If asked to repeat twice in a row, change topic instead
            return ResponseGeneratorResult(text=f"{self.choose(SORRY_FOR_CONNECTION)}", #..."anyway, I was thinking.... [prompt continues]"
                                    priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                    state=self.state if self.state is not None else self.State(), cur_entity=self.get_current_entity(),
                                    conditional_state=self.ConditionalState())
        return ResponseGeneratorResult(
            text=f"{self.choose(response_lists.CLARIFICATION_COMPLAINT_RESPONSE)} {last_sentence}",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )

    def handle_repetition_complaint(self, slots):
        return ResponseGeneratorResult(
            text=self.choose(response_lists.REPETITION_COMPLAINT_RESPONSE),
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=True,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )

    def handle_privacy_complaint(self, slots):
        return ResponseGeneratorResult(
            text=self.choose(response_lists.PRIVACY_COMPLAINT_RESPONSE),
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=True,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )

    def handle_generic_complaint(self, slots):
        return ResponseGeneratorResult(
            text=self.choose(response_lists.GENERIC_COMPLAINT_RESPONSE),
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=False,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )

    def handle_personal_issue(self, slots):
        # overridden by NEURAL CHAT only
        return None

    def handle_anything(self, slots):
        """slots is just boolean for this handler"""
        return ResponseGeneratorResult(
            text=self.choose(['Okay!', 'Alright!', 'Hmm let me think.']),
            priority=ResponsePriority.CAN_START,
            needs_prompt=True,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )

    def handle_you_cant_do_that_complaint(self, slots):
        return ResponseGeneratorResult(
            text="I'm sorry, I might've misspoke. Let's move on to something else.",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=True,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )

    def handle_doesnt_make_sense_complaint(self, slots):
        return ResponseGeneratorResult(
            text="I'm sorry, I might've misspoke. Let's move on to something else.",
            priority=ResponsePriority.STRONG_CONTINUE,
            needs_prompt=True,
            state=self.state if self.state is not None else self.State(),
            cur_entity=self.get_current_entity(),
            conditional_state=self._construct_no_update_conditional_state()
        )

    def handle_user_complaint(self):
        complaint_handlers = {
            (lambda: misheard_complaint(self.state_manager)): self.handle_misheard_complaint,
            (lambda: unclear_complaint(self.state_manager)): self.handle_unclear_complaint,
            (lambda: repetition_complaint(self.state_manager)): self.handle_repetition_complaint,
            (lambda: privacy_complaint(self.state_manager)): self.handle_privacy_complaint,
            (lambda: you_cant_do_that_complaint(self.state_manager)): self.handle_you_cant_do_that_complaint,
            (lambda: doesnt_make_sense_complaint(self.state_manager)): self.handle_doesnt_make_sense_complaint,
            (lambda: generic_complaint(self.state_manager)): self.handle_generic_complaint
        }
        for complaint_detector, complaint_handler in complaint_handlers.items():
            matching_slots = complaint_detector()
            if matching_slots:
                response = complaint_handler(matching_slots)
                logger.primary_info(f"User complaint detected in {complaint_handler.__name__} with available slots {matching_slots}")
                return response
        logger.primary_info(f"No user complaints detected.")

    def handle_abrupt_user_initiative(self):
        initiative_handlers = { # NOTE: there's a hand-wavey order to these but no rigorous rules.
            (lambda: user_asked_about_weather(self.state_manager)): self.handle_weather,
            (lambda: user_asked_about_time(self.state_manager)): self.handle_what_time,
            (lambda: user_requested_repetition(self.state_manager)): self.handle_repetition_request, # needs to be before ALEXA COMMAND because play what / play that again
            # (lambda: user_said_alexa_command(self.state_manager)): self.handle_alexa_command, removing for now (ERIC)
            (lambda: user_wants_name_correction(self.state_manager)): self.handle_user_name_correction,
            (lambda: user_requested_name(self.state_manager)): self.handle_name_request,
            (lambda: user_got_cutoff(self.state_manager)): self.handle_cutoff_user,
            (lambda: user_asked_for_our_age(self.state_manager)): self.handle_age_request,
            (lambda: user_requested_clarification(self.state_manager)): self.handle_user_clarification,
            (lambda: user_asked_ablities_question(self.state_manager)): self.handle_abilities_question,
            (lambda: user_asked_personal_question(self.state_manager)): self.handle_personal_question,
            (lambda: user_interrupted(self.state_manager)): self.handle_interruption_question,
            (lambda: user_said_chatty_phrase(self.state_manager)): self.handle_chatty_phrase,
            (lambda: user_asked_for_story(self.state_manager)): self.handle_story_request,
            (lambda: user_shared_personal_problem(self.state_manager)): self.handle_personal_issue,
            (lambda: user_said_anything(self.state_manager)): self.handle_anything
        }

        for initiative_handling_condition, initiative_handler in initiative_handlers.items():
            matching_slots = initiative_handling_condition()
            if matching_slots:
                response = initiative_handler(matching_slots)
                logger.primary_info(f"Abrupt initiative detected in {initiative_handler.__name__} with available slots {matching_slots}")
                return response
        logger.primary_info(f"No abrupt initiative detected.")

    def handle_default_pre_checks(self):
        """
        @deprecated, hopefully

        This is mainly for RGs that can activate on any turn and where it does not matter if it was already active
        in the last turn, i.e. 'memoryless' RGs. Examples includes ALEXA_COMMANDS and ONE_TURN_HACK.
        :return:
        """
        return None

    def handle_default_post_checks(self) -> Optional[ResponseGeneratorResult]:
        """
        This is mainly for RGs that can activate on any turn and where it does not matter if it was already active
        in the last turn, i.e. 'memoryless' RGs. Examples includes ALEXA_COMMANDS and ONE_TURN_HACK.
        :return:
        """
        return None

    def handle_custom_continuation_checks(self) -> Optional[ResponseGeneratorResult]:
        """
        This is run only when the RG was active in the last turn.
        :return:
        """
        return None

    def is_first_turn(self):
        return self.get_last_active_rg() != self.name

    def prompted_last_turn(self):
        if self.state_manager.last_state is not None:
            return self.state_manager.last_state.selected_prompt_rg == self.name

    def responded_last_turn(self):
        if self.state_manager.last_state is not None:
            return self.state_manager.last_state.selected_response_rg == self.name

    def active_last_turn(self):
        return self.get_last_active_rg() == self.name

    def get_last_rg_in_control(self) -> Optional[str]:
        """
        If a prompt was used last turn, the RG that generated the selected prompt is in control.
        Otherwise, the RG that generated the response is in control.
        :return:
        """
        if self.state_manager.last_state is not None:
            prev_selected_prompt_rg = self.state_manager.last_state.selected_prompt_rg
            if prev_selected_prompt_rg is not None:
                return prev_selected_prompt_rg
            else:
                return self.state_manager.last_state.selected_response_rg


    def get_response(self, state) -> ResponseGeneratorResult:
        response_types = self.identify_response_types(self.utterance)
        logger.primary_info(f"{self.name} identified response_types: {response_types}")
        self.state = state
        self.response_types = response_types
        self.set_cache(f'{self.name}_response_types', response_types)
        self.handle_user_attributes()

        logger.info(f"{self.name} state is: {state} and has response types {self.response_types}")
        logger.info(f"Last active RG: {self.get_last_active_rg()}, last prompt RG: {self.get_last_prompt_rg()}")

        response = self.handle_default_pre_checks()
        if response: return self.possibly_augment_with_prompt(response)

        is_continuing_conversation = (self.get_last_rg_in_control() == self.name)
        if is_continuing_conversation:
            logger.primary_info(f"Before checking for CHANGE_TOPIC, {self.name} is supposed to continue convo")
        # special check for topic changes

        if is_continuing_conversation and ResponseType.CHANGE_TOPIC in response_types:
            res = self.handle_change_topic()
            if res is None:
                pass
            elif isinstance(res, ResponseGeneratorResult):
                return self.possibly_augment_with_prompt(res)
            elif res is False:
                logger.primary_info(f"{self.name}: user asked to change topic, so we stop the conversation and continue.")
                state = self.update_state_if_not_chosen(self.state, self.ConditionalState())
                self.state = state
                is_continuing_conversation = False

        if is_continuing_conversation:
            logger.primary_info(f"{self.name} is already active, so checking if it should continue")

            current_rg_response_handlers = {
                (lambda: True): self.handle_user_complaint,
                (lambda: True): self.handle_abrupt_user_initiative,
                (lambda: ResponseType.REQUEST_REPEAT in response_types): self.handle_repeat_request,
                (lambda: ResponseType.COMPLAINT in response_types): self.handle_complaint,
                (lambda: ResponseType.DISINTERESTED in response_types): self.handle_rejection_response,
                (lambda: ResponseType.QUESTION in response_types): self.handle_question,
                (lambda: True): self.handle_custom_continuation_checks,
                (lambda: True): wrapped_partial(self.continue_conversation, response_types)
            }

            for response_condition, response_handler in current_rg_response_handlers.items():
                if response_condition():
                    response = response_handler()
                    if response:
                        logger.primary_info(f"{self.name} received a response from: {response_handler.__name__}")
                        return self.possibly_augment_with_prompt(response)

        if not is_continuing_conversation: # allow the first branch to divert here
            logger.primary_info(f"{self.name} is not currently active, so checking if it should activate")

            activation_check_fns = {
                (lambda: self.get_last_active_rg() in self.disallow_start_from): self.get_fallback_result,
                (lambda: True): self.handle_direct_navigational_intent,
                (lambda: True): self.handle_current_entity,
                (lambda: True): self.get_intro_treelet_response,
                (lambda: True): self.handle_custom_activation_checks,
            }

            for activation_condition, activation_check_fn in activation_check_fns.items():
                if activation_condition():
                    response = activation_check_fn()
                    if response: return self.possibly_augment_with_prompt(response)

        response = self.handle_default_post_checks()
        if response:
            return self.possibly_augment_with_prompt(response)

        return self.get_fallback_result()


    def possibly_augment_with_prompt(self, response):
        """
        Only for RGs that use internal prompts, e.g. MUSIC/FOOD.
        Will do nothing unless ConditionalState object contains a 'prompt_treelet' attribute.
        :param response:
        :return:
        """
        logger.primary_info(f"Possibly augmenting {response}")
        prompt_treelet_str = self.get_internal_prompt(response)
        logger.info(f"{self.name} received an internal prompt treelet name: {prompt_treelet_str}")
        if prompt_treelet_str:
            treelet = self.treelets[prompt_treelet_str]
            logger.info(f"Received an internal prompt treelet: {treelet}")
            try:
                prompt = treelet.get_prompt(conditional_state=response.conditional_state)
            except TypeError: # wrong # of arguments
                prompt = treelet.get_prompt()
            logger.info(f"Received an internal prompt: {prompt}")
            if prompt:
                response.text = f"{response.text} {prompt.text}"
                response.state = prompt.state
                response.conditional_state = prompt.conditional_state
                response.cur_entity = prompt.cur_entity
                response.expected_type = prompt.expected_type
                response.conditional_state.next_treelet_str = prompt_treelet_str
                logger.info(f"Now response.state = {response.state}")
        return response

    def continue_conversation(self, response_types) -> Optional[ResponseGeneratorResult]:
        logger.info(f"Attempting to continue conversation from {self.name} with response types: {response_types}")
        prev_treelet_str = self.state.prev_treelet_str
        next_treelet_str = self.state.next_treelet_str

        next_treelet = None
        response_priority = ResponsePriority.STRONG_CONTINUE

        if next_treelet_str is None:
            return self.emptyResult() # continue from some other RG
        elif next_treelet_str == '':
            return None
        elif next_treelet_str == 'transition':
            treelet_matrix = self.transition_matrix.get(prev_treelet_str, None)
            assert treelet_matrix is not None
            logger.info(f"Continuing conversation from {prev_treelet_str}: treelet matrix is {treelet_matrix}")
            for key, val in treelet_matrix.items():
                if 'ResponseType' in str(type(key)): # hack because isinstance(key, ResponseType) will not work with the 'inherited' response types
                    if key in response_types:
                        logger.info(f"Matched response type: {key}")
                        if isinstance(val, ResponseGeneratorResult):
                            return val
                        elif callable(val): # allow for dynamically generated responses
                            return val()
                        else:
                            next_treelet, response_priority = val
                            break
                else: # key = lambda (state, response_types)
                    if key(self.state, response_types):
                        if isinstance(val, ResponseGeneratorResult):
                            return val
                        elif callable(val): # allow for dynamically generated responses
                            return val()
                        else:
                            next_treelet, response_priority = val
                            break

        elif next_treelet_str == 'any':
            response_priority = ResponsePriority.STRONG_CONTINUE
            for treelet in self.treelets.values():
                proposed_response = treelet.get_response(response_priority, )
                if proposed_response:
                    next_treelet = treelet
        elif next_treelet_str == 'exit':
            return self.handle_exit_response()
        else: # next_treelet_str specifies one of the treelets
            logger.info(f"Continuing conversation from {next_treelet_str} for {self.name}")
            assert next_treelet_str in self.treelets
            next_treelet = self.treelets[next_treelet_str]
            response_priority = ResponsePriority.STRONG_CONTINUE

        if next_treelet is not None:
            response = next_treelet.get_response(response_priority, )
            if response: return response
        return None

    # def get_known_treelet(self) -> str:
    #     """Gets the treelet that should respond, given the state."""
    #     responding_treelet = getattr(self.state, 'responding_treelet', None)
    #     if responding_treelet: return responding_treelet

    def handle_current_entity_for_prompt(self) -> Optional[PromptResult]:
        current_entity = self.get_current_entity(initiated_this_turn=True)
        if current_entity:
            treelet_str = self.get_treelet_for_entity(current_entity)
            if treelet_str is not None:
                treelet = self.treelets[treelet_str]
                prompt = treelet.get_prompt()
                if prompt:
                    logger.info(f"{self.name} found contextual entity prompt")
                    return prompt
        return None

    def handle_smooth_handoff(self) -> Optional[PromptResult]:
        return None

    def handle_misc_prompt_checks(self) -> Optional[PromptResult]:
        return None

    def get_prompt(self, state) -> PromptResult:
        logger.info(f"{self.name} is running get_prompt()")
        self.state = state
        self.response_types = self.get_cache(f'{self.name}_response_types')

        if not self.can_give_prompts:
            return self.emptyPrompt()

        if self.get_last_active_rg() in self.disallow_start_from:
            return self.emptyPrompt()

        if state.next_treelet_str is None: # we are exiting from this RG
            return self.emptyPrompt()

        prompt = self.handle_smooth_handoff()
        if prompt: return prompt

        logger.info(f"{self.name} checking for contextual entity prompt")
        # contextual prompt
        prompt = self.handle_current_entity_for_prompt()
        if prompt:
            logger.info(f"{self.name} found contextual entity prompt.")
            return prompt

        # intro prompt
        logger.info(f"{self.name} Checking for intro prompt")
        prompt = self.get_intro_prompt()
        if prompt:
            logger.info(f"{self.name} found intro prompt")
            return prompt

        prompt = self.handle_misc_prompt_checks()
        if prompt: return prompt

        return self.emptyPrompt()

    def get_intro_prompt(self) -> Optional[PromptResult]:
        """
        Prompt that starts off the RG
        :return:
        """
        logger.info(f"Iterating through treelets for prompts for {self.name}")
        for treelet in self.treelets.values():
            proposed_prompt = treelet.get_prompt()
            if proposed_prompt:
                logger.info(f"{self.name} found a prompt!")
                return proposed_prompt
            else:
                logger.info(f"{self.name} found no prompt.")

    def get_current_state(self):
        return self.state_manager.current_state

    def get_general_prompt(self):
        return None

    def get_fallback_result(self):
        return self.emptyResult_with_conditional_state()

    # For 'prompt-driven' RG's. Returns the name of a treelet, or None if none is found.
    def get_internal_prompt(self, proposed_response):
        logger.info(f"{self.name} asked for an internal prompt. Current response is {proposed_response}")
        # if self.name == 'FOOD': import pdb; pdb.set_trace()
        if getattr(proposed_response.conditional_state, 'prompt_treelet', NO_UPDATE) != NO_UPDATE:
            return proposed_response.conditional_state.prompt_treelet
        return None

    @property
    def utterance(self):
        return self.state_manager.current_state.text

    @property
    def response_types(self):
        # logger.info(f"Fetching response types: {self._response_types}")
        return self._response_types

    @response_types.setter
    def response_types(self, new_response_types):
        # logger.info(f"Setting response types from {self.response_types} to {new_response_types} in {self.name}")
        self._response_types = new_response_types

    """
    Handlers for specific user behaviors
    """
    def handle_user_attributes(self):
        """
        Based on the state and the user's utterance, set user attributes as desired.
        This method is a NO-OP by default and should be overridden.
        :return:
        """
        return

    def handle_rejection_response(self, prefix='', main_text=None, suffix='',
                                  priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                  conditional_state=None, answer_type=AnswerType.ENDING):
        if main_text is None:
            if prefix == '':
                # choose responses with their own prefixes
                main_text = self.choose([
                    "Alright, let's move on to something else then.",
                    "Okay no problem, let's move on.",
                    "Okay sure, let me think about what we haven't talked about yet."
                ])
            else:
                main_text = self.choose([
                    "Let's move on to something else then.",
                    "Let's talk about something else.",
                    "We can talk about something else."
                ])
        logger.primary_info(f"{self.name} received rejection response, so resetting state to null (currently) {self.state}")
        state = self.update_state_if_not_chosen(self.state, conditional_state if conditional_state else self._construct_no_update_conditional_state())
        return ResponseGeneratorResult(
            text=f"{prefix} {main_text} {suffix}",
            priority=priority,
            needs_prompt=needs_prompt, state=state,
            cur_entity=None,
            no_transition=True,
            conditional_state=conditional_state if conditional_state else self._construct_no_update_conditional_state(),
            answer_type=answer_type
        )

    def _construct_no_update_conditional_state(self):
        retval = self.ConditionalState()
        for attr in dir(retval):
            if not callable(getattr(retval, attr)) and not attr.startswith("__"):
                setattr(retval, attr, NO_UPDATE)
        return retval

    def handle_repeat_request(self):
        return self.handle_repetition_request({})
        # prefix = "Sorry if I wasn't clear. What I said was: " # TODO: robustify this?
        # response = self.get_previous_bot_utterance()
        # if prefix not in response: response = prefix + response
        # return ResponseGeneratorResult(
        #     text=response,
        #     priority=ResponsePriority.STRONG_CONTINUE,
        #     needs_prompt=False, state=self.state,
        #     cur_entity=self.get_current_entity(),
        #     conditional_state=self._construct_no_update_conditional_state()
        # )

    def handle_complaint(self) -> Optional[ResponseGeneratorResult]:
        return None

    def choose(self, items):
        """
        Choose from a list of responses the response that is the least repetitive
        :param items:
        :return:
        """
        return self.state_manager.current_state.choose_least_repetitive(items)

    def set_cache(self, key, value):
        self.state_manager.current_state.set_cache(key, value)

    def get_cache(self, key):
        return self.state_manager.current_state.get_cache(key)

    def get_smooth_handoff(self):
        return self.state_manager.current_state.smooth_handoff

    def get_sentiment(self):
        return self.state_manager.current_state.corenlp['sentiment']

    def get_experiments(self):
        return self.state_manager.current_state.experiments

    def get_experiment_by_lookup(self, experiment_name):
        expts = self.get_experiments()
        return expts.look_up_experiment_value(experiment_name)

    def get_acknowledgement(self, cur_entity, allow_neural=False):
        for ent_group_name, ent_group in ENTITY_GROUPS_FOR_CLASSIFICATION.ordered_items:
            if ent_group.matches(cur_entity) and ent_group_name in ACKNOWLEDGMENT_DICTIONARY:
                logger.primary_info(f'cur_entity {cur_entity} matches EntityGroup "{ent_group_name}" which we have an acknowledgment for, so giving acknowledgment')
                acknowledgments = [a.format(entity=cur_entity.common_name) for a in ACKNOWLEDGMENT_DICTIONARY[ent_group_name]]
                acknowledgment = self.choose(acknowledgments)
                return acknowledgment
        if allow_neural:
            ack = get_random_fallback_neural_response(self.get_current_state())
            return ack

    def get_sentence_segments(self, text):
        sentseg = NLTKSentenceSegmenter(self.state_manager)
        return list(sentseg.execute(text))
