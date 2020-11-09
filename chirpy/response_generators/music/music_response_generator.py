# Standard library imports
import random
from typing import Optional
import traceback
from collections import namedtuple

# Core imports
# from cobot_core.service_module import LocalServiceModule # TODO remove legacy code
from chirpy.core.callables import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.core.response_generator_datatypes import emptyResult, emptyPrompt, UpdateEntity

# Music RG imports
from chirpy.response_generators.music.state import State
from chirpy.response_generators.music.utils import logger, WikiEntityInterface
from chirpy.response_generators.music.treelets.abstract_treelet import Treelet
from chirpy.response_generators.music.treelets.generic_treelet import GenericTreelet
from chirpy.response_generators.music.treelets.genre_treelet import GenreTreelet
from chirpy.response_generators.music.treelets.instrument_treelet import InstrumentTreelet
from chirpy.response_generators.music.treelets.musician_treelet import MusicianTreelet
from chirpy.response_generators.music.treelets.song_treelet import SongTreelet
from chirpy.response_generators.music.expression_lists import QUESTION_CONNECTORS, TOPIC_CHANGING_SIGNALS, ChatTemplate


TURN_THRESHOLD = 3


class MusicResponseGenerator(ResponseGenerator):

    name = 'MUSIC'

    def __init__(self, state_manager) -> None:
        super().__init__(state_manager)
        treelets = [
            #GenreTreelet(self),
            GenericTreelet(self),
            # InstrumentTreelet(self),
            MusicianTreelet(self),
            SongTreelet(self)
        ]
        self.treelets = {treelet.__name__(): treelet for treelet in treelets}
        self.state = State()
        self.name = 'MUSIC'

    def init_state(self) -> State:
        return self.state

    def update_state(self, state) -> State:
        self.state = state

    def get_response(self, state: State) -> ResponseGeneratorResult:
        # try:
        #     response = self._get_response(state)
        # except Exception as err:
        #     tb = traceback.print_tb(err.__traceback__)
        #     logger.error("MUSIC RG is returning an emptyResult, because of {}, with the traceback: {}".format(err, tb))
        #     response = emptyResult(state)
        # return response

        return self._get_response(state)

    def _get_response(self, state: State) -> ResponseGeneratorResult:
        # Update the state.
        self.update_state(state)

        # Variables tracking whether we can respond to cur_entity or phrases.
        trigger_entity_treelet_name = None
        trigger_entity = None
        trigger_phrase = None

        # Check if there is a treelet that can respond to the user initiated cur_entity, if it exists.
        # We filter the discussed entities here.
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity
        current_state = self.state_manager.current_state
        user_initiated = current_state.entity_tracker.cur_entity_initiated_by_user_this_turn(current_state)
        if user_initiated and cur_entity and cur_entity not in state.discussed_entities:
            trigger_entity_treelet_name = self._get_treelet_name_for_entity(cur_entity)
            if trigger_entity_treelet_name: trigger_entity = cur_entity

        # Check if the user explicitly requests one of the treelets
        utterance = self.state_manager.current_state.text
        chat_slots = ChatTemplate().execute(utterance)

        # Set state.cur_treelet if there is a treelet that can handle the user utterance.
        top_dialog_act = current_state.dialog_act['top_1']
        neg_intent = self.state_manager.current_state.navigational_intent.neg_intent
        pos_topic = self.state_manager.current_state.navigational_intent.pos_topic
        last_rg = self.state_manager.last_state_active_rg

        if self.state_manager.current_state.question['is_question']:
            logger.primary_info('We got a question, so Music RG is returning an empty response.')
            #handoff_response = Treelet.get_handoff_response(self.state_manager, state)
            return emptyResult(state)
        elif last_rg == self.name and (neg_intent or top_dialog_act == 'abandon'):
            logger.primary_info('NavigationalIntent is negative, so Music RG is ending the conversation and asking for prompts.')
            handoff_response = Treelet.get_handoff_response(self.state_manager, state)
            handoff_response.priority = ResponsePriority.STRONG_CONTINUE
            return handoff_response
        elif trigger_entity_treelet_name:
            logger.primary_info('{} can handle the cur_entity {}, so Music RG will generate a response.'.format(trigger_entity_treelet_name, trigger_entity))
            if trigger_entity_treelet_name != state.cur_treelet:
                state = self.update_state_if_not_chosen(state)
            state.cur_treelet = trigger_entity_treelet_name
        elif pos_topic or chat_slots:
            if pos_topic:
                phrase = pos_topic[0]
            else:
                phrase = chat_slots['trigger_word']

            treelets_for_phrase = [name for name, treelet in self.treelets.items() if phrase in treelet.trigger_phrases]
            if treelets_for_phrase:
                logger.primary_info('{} can handle the positive navigation with the topic {}, so Music RG will generate a response.'.format(treelets_for_phrase[0], phrase))
                if treelets_for_phrase[0] != state.cur_treelet:
                    state = self.update_state_if_not_chosen(state)
                state.cur_treelet = treelets_for_phrase[0]
                trigger_phrase = phrase
            else:
                logger.primary_info('Music RG cannot handle the positive navigation with the topic {}, so returning an empty response.'.format(phrase))
                state.cur_treelet = None

        # If no treelet can handle the user utterance, return an empty response.
        if not state.cur_treelet:
            logger.primary_info('None of the Music RG treelets can handle the user utterance. Returning an empty response.')
            return emptyResult(state)

        # Get the response from the specified treelet.
        cur_treelet = self.treelets[state.cur_treelet]
        logger.primary_info('{} treelet in Music RG will generate a response.'.format(cur_treelet))
        response = cur_treelet.get_response(state, trigger_entity=trigger_entity, trigger_phrase=trigger_phrase)

        number_of_turns = len(response.state.treelet_history) + 1

        if response.conditional_state.needs_internal_prompt:
            if number_of_turns > TURN_THRESHOLD:
                response.conditional_state.next_treelet = None
            else:
                prompt = self._get_random_prompt(state, conditional_state=response.conditional_state)
                if prompt:
                    #response.text = self._add_connector(self.state_manager, response.text, prompt.text, connector_probability=1)
                    response.text = "{} {}".format(response.text, prompt.text)
                    response.state = prompt.state
                    response.conditional_state = prompt.conditional_state
                    response.cur_entity = prompt.cur_entity
                    response.expected_type = prompt.expected_type
                else:
                    response.conditional_state.next_treelet = None
                    # We don't have any internal prompt remaining and the last RG was not music.
                    if last_rg != self.name:
                        return emptyResult(state)

        if not response.conditional_state.next_treelet:
            response.needs_prompt = True
            response.conditional_state.needs_external_prompt = True

        return response

    def get_prompt(self, state: dict) -> PromptResult:
        try:
            response = self._get_prompt(state)
        except Exception as err:
            tb = traceback.print_tb(err.__traceback__)
            logger.error("MUSIC RG is returning an emptyPrompt, because of {}, with the traceback: {}".format(err, tb))
            response = emptyPrompt(state)
        return response

    def _get_prompt(self, state: dict) -> PromptResult:
        prompt = None

        # Check if there is a treelet that can respond to the user initiated cur_entity, if it exists.
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity
        if cur_entity and cur_entity not in state.discussed_entities:
            entity_treelet_name = self._get_treelet_name_for_entity(cur_entity)
            if entity_treelet_name:
                prompt = self.treelets[entity_treelet_name].get_prompt(state, trigger_entity=cur_entity)

        # Check if there is a random treelet that can respond.
        if not prompt: prompt = self._get_random_prompt(state)

        # If we have a prompt, pick a connector.
        if not prompt:
            prompt = emptyPrompt(state)
        else:
            # change_signal = self.state_manager.choose_least_repetitive(TOPIC_CHANGING_SIGNALS)
            change_signal = random.choice(TOPIC_CHANGING_SIGNALS)
            prompt.text = "{} {}".format(change_signal, prompt.text)
            prompt.text = prompt.text

        return prompt

    def update_state_if_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        state.treelet_history.append(conditional_state.turn_treelet_history)
        state.cur_treelet = conditional_state.next_treelet
        state.musician_entity = conditional_state.musician_entity
        state.song_entity = conditional_state.song_entity
        state.acknowledged_entity = conditional_state.acknowledged_entity
        if conditional_state.asked_question:
            state.last_turn_asked_question = conditional_state.asked_question
            state.asked_questions.append(state.last_turn_asked_question)
        if conditional_state.used_question:
            state.asked_questions.append(conditional_state.used_question)
        if conditional_state.discussed_entities:
            state.discussed_entities.extend(conditional_state.discussed_entities)
        if conditional_state.needs_external_prompt:
            state = self.update_state_if_not_chosen(state)
        if conditional_state.repeated_question:
            state.num_repeats += 1
        return state

    @staticmethod
    def update_state_if_not_chosen(state: dict, conditional_state: Optional[dict] = None) -> dict:
        state.treelet_history = []
        state.cur_treelet = None
        state.last_turn_asked_question = None
        state.musician_entity = None
        state.song_entity = None
        state.num_repeats = 0
        state.acknowledged_entity = False
        return state

    @staticmethod
    def get_entity(state) -> UpdateEntity:
        return UpdateEntity(False) # TODO minor check

    @staticmethod
    def _add_connector(state_manager, first, second, connector_probability = 0.5):
        if not connector_probability is 0:
            number_of_options = int(1 / connector_probability)
            options = list(range(0, number_of_options))
            if 0 is random.choice(options):
                connector = state_manager.choose_least_repetitive(QUESTION_CONNECTORS)
                connector = random.choice(QUESTION_CONNECTORS)
                return f"{first} {connector} {second}"
        return f"{first} {second}"

    def _get_random_prompt(self, state, conditional_state=None):
        prompt = None
        treelet_names = list(self.treelets.keys())
        random.shuffle(treelet_names)
        for treelet_name in treelet_names:
            if not prompt: prompt = self.treelets[treelet_name].get_prompt(state, conditional_state=conditional_state)
        return prompt

    def _get_treelet_name_for_entity(self, entity):
        entity_treelet_name = None
        for treelet_name, treelet in self.treelets.items():
            for entity_group in treelet.trigger_entity_groups:
                if WikiEntityInterface.is_in_entity_group(entity, entity_group):
                    if not entity_treelet_name:
                        entity_treelet_name = treelet_name
        return entity_treelet_name