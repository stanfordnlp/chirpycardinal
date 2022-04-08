from collections import defaultdict

import datetime
import jsonpickle
import logging
import os
import uuid
import time
from typing import Dict

from chirpy.response_generators.launch.launch_response_generator import LaunchResponseGenerator
from chirpy.response_generators.fallback.fallback_response_generator import FallbackResponseGenerator
#from chirpy.response_generators.red_question.red_question_response_generator import RedQuestionResponseGenerator
from chirpy.response_generators.offensive_user.offensive_user_response_generator import OffensiveUserResponseGenerator
from chirpy.response_generators.wiki2.wiki_response_generator import WikiResponseGenerator
from chirpy.response_generators.food.food_response_generator import FoodResponseGenerator
from chirpy.response_generators.opinion2.opinion_response_generator import OpinionResponseGenerator2
from chirpy.response_generators.neural_chat.neural_chat_response_generator import NeuralChatResponseGenerator
from chirpy.response_generators.categories.categories_response_generator import CategoriesResponseGenerator
from chirpy.response_generators.neural_fallback.neural_fallback_response_generator import NeuralFallbackResponseGenerator
from chirpy.response_generators.closing_confirmation.closing_confirmation_response_generator import ClosingConfirmationResponseGenerator

## TODO: fix the PSQL endpoint
from chirpy.response_generators.music.music_response_generator import MusicResponseGenerator
from chirpy.response_generators.acknowledgment.acknowledgment_response_generator import AcknowledgmentResponseGenerator
from chirpy.response_generators.personal_issues.personal_issues_response_generator import PersonalIssuesResponseGenerator
from chirpy.response_generators.aliens.aliens_response_generator import AliensResponseGenerator
from chirpy.response_generators.transition.transition_response_generator import TransitionResponseGenerator

from chirpy.annotators.corenlp import CorenlpModule
from chirpy.annotators.navigational_intent.navigational_intent import NavigationalIntentModule
from chirpy.annotators.stanfordnlp import StanfordnlpModule
from chirpy.annotators.coref import CorefAnnotator
from chirpy.annotators.emotion import EmotionAnnotator
from chirpy.annotators.g2p import NeuralGraphemeToPhoneme
from chirpy.annotators.gpt2ed import GPT2ED
from chirpy.annotators.question import QuestionAnnotator
from chirpy.annotators.blenderbot import BlenderBot
import chirpy.core.flags as flags
from chirpy.core.util import get_function_version_to_display
from chirpy.annotators.dialogact import DialogActAnnotator
from chirpy.core.entity_linker.entity_linker import EntityLinkerModule

import chirpy.core.flags as flags
from chirpy.core.latency import log_events_to_dynamodb, measure, clear_events
from chirpy.core.regex.templates import StopTemplate
from chirpy.core.handler import Handler
from chirpy.core.logging_utils import setup_logger, update_logger, PROD_LOGGER_SETTINGS

# Timeout at the highest level, as close as possible to 10 seconds. Do nothing after, just create an apologetic
# response and send it over
OVERALL_TIMEOUT = 9.75 if flags.use_timeouts else flags.inf_timeout  # seconds

# Timeout for final_response function. Set at 9.35 seconds to comfortably log the latencies
FINAL_RESPONSE_TIMEOUT = 9.35 if flags.use_timeouts else flags.inf_timeout  #seconds

# Timeout for progressive response
PROGRESSIVE_RESPONSE_TIMEOUT = 3 if flags.use_timeouts else flags.inf_timeout  #seconds

# Timeout for NLP Pipeline
NLP_PIPELINE_TIMEOUT = 3 if flags.use_timeouts else flags.inf_timeout  #seconds

LATENCY_EXPERIMENT = False
LATENCY_BINS = [0, 1, 1.5, 2, 2.5]

DEFAULT_REPROMPT = "Sorry, I don't think I understood. Could you repeat that please?".strip()

logger = logging.getLogger('chirpylogger')
apology_string = 'Sorry, I\'m having a really hard time right now. ' + \
'I have to go, but I hope you enjoyed our conversation so far. ' + \
'Have a good day!'

state_store = {}
user_store = defaultdict(dict)

class StateTable:
    def __init__(self):
        self.table_name = 'StateTable'

    def fetch(self, session_id, creation_date_time):
        #logger.warning(f"state_table fetching last state for session {session_id}, creation_date_time {creation_date_time} from table {self.table_name}")
        if session_id is None:
            return None
        try:
            item = None
            start_time = time.time()
            timeout = 2 #second
            while (item is None and time.time() < start_time + timeout):
                a = list(state_store.keys())[0]
                Q = '"'
                return state_store[(Q + session_id + Q, creation_date_time)]
            if item is None:
                #logger.error(
                #    f"Timed out when fetching last state\nfor session {session_id}, creation_date_time {creation_date_time} from table {self.table_name}.")
                pass
            else:
                return item
        except:
            logger.error("Exception when fetching last state")
            return None

    def persist(self, state: Dict):
        logger.primary_info('Using StateTable to persist state! Persisting to table {}'.format(self.table_name))
        logger.primary_info('session_id: {}'.format(state['session_id']))
        logger.primary_info('creation_date_time: {}'.format(state['creation_date_time']))
        try:
            assert 'session_id' in state
            assert 'creation_date_time' in state
            global state_store
            state_store[(state['session_id'], state['creation_date_time'])] = state
            return True
        except:
            logger.error("Exception when persisting state to table" + self.table_name, exc_info=True)
            return False

class UserTable():
    def __init__(self):
        self.table_name = 'UserTable'

    def fetch(self, user_id):
        logger.debug(
            f"user_table fetching last state for user {user_id} from table {self.table_name}")
        if user_id is None:
            return None
        try:
            item = None
            start_time = time.time()
            timeout = 2  # second
            while (item is None and time.time() < start_time + timeout):
                item = user_store[user_id]
            if item is None:
                logger.error(
                    f"Timed out when fetching user attributes\nfor user_id {user_id} from table {self.table_name}.")
            else:
                return item
        except:
            logger.error("Exception when fetching user attributes from table: " + self.table_name,
                         exc_info=True)
            return None

    def persist(self, user_attributes: Dict) -> None:
        """
        This will take the provided user_preferences object and persist it to DynamoDB. It does this by creating
                a dictionary representing the DynamoDB item to push consisting of user_id and a dictionary representing all of
                the user preferences.
        :param user_attributes: input UserAttributes object
        :return: None
        """
        try:
            assert 'user_id' in user_attributes
            global user_store
            user_store[user_attributes['user_id']] = user_attributes
            return True
        except:
            logger.error("Exception when persisting state to table: " + self.table_name, exc_info=True)
            return False

class LocalAgent():
    """
    Agent that inputs and outputs text, and runs callables locally.
    """
    def __init__(self):
        self.state_table = StateTable()
        self.user_table = UserTable()
        self.session_id = uuid.uuid4().hex
        self.user_id = "1"
        self.new_session = True
        self.last_state_creation_time = None

    def should_end_session(self, turn_result):
        return turn_result.should_end_session

    def should_launch():
        return True

    def get_state_attributes(self, user_utterance):
        state_attributes = {}
        state_attributes['creation_date_time'] = str(datetime.datetime.utcnow().isoformat())
        pipeline = os.environ.get('PIPELINE')
        state_attributes['pipeline'] = pipeline if pipeline is not None else ''
        commit_id = os.environ.get('COMMITID')
        state_attributes['commit_id'] = commit_id if commit_id is not None else ''
        state_attributes['session_id'] = self.session_id
        state_attributes['user_id'] = self.user_id
        state_attributes['text'] = user_utterance
        state_attributes = {k: jsonpickle.encode(v) for k, v in state_attributes.items()}
        return state_attributes

    def get_user_attributes(self):
        user_attributes = self.user_table.fetch(self.user_id)
        user_attributes['user_id'] = self.user_id
        user_attributes['user_timezone'] = None
        user_attributes = {k: jsonpickle.encode(v) for k, v in user_attributes.items()}
        return user_attributes

    def get_last_state(self): # figure out new session and session_id
        if not self.new_session:
            last_state = self.state_table.fetch(self.session_id, self.last_state_creation_time)
        else:
            last_state = None
        return last_state

    def create_handler(self):
        return Handler(
                response_generator_classes=[LaunchResponseGenerator, FallbackResponseGenerator,
                                            NeuralFallbackResponseGenerator,
                                            NeuralChatResponseGenerator,
                                            OffensiveUserResponseGenerator,
                                            CategoriesResponseGenerator,
                                            ClosingConfirmationResponseGenerator,
                                            AcknowledgmentResponseGenerator,
                                            PersonalIssuesResponseGenerator,
                                            OpinionResponseGenerator2,
                                            AliensResponseGenerator,
                                            TransitionResponseGenerator,
                                            FoodResponseGenerator,
                                            WikiResponseGenerator,
                                            MusicResponseGenerator,
                                            ],
            annotator_classes = [QuestionAnnotator, DialogActAnnotator, NavigationalIntentModule, StanfordnlpModule, CorenlpModule,
                                 EntityLinkerModule, BlenderBot],
            annotator_timeout = NLP_PIPELINE_TIMEOUT
        )

    def process_utterance(self, user_utterance):

        # create handler (pass in RGs + annotators)
        handler = self.create_handler()

        current_state = self.get_state_attributes(user_utterance)
        user_attributes = self.get_user_attributes()
        last_state = self.get_last_state()

        turn_result = handler.execute(current_state, user_attributes, last_state)
        response = turn_result.response
        try:
            # create new state? -> what do we need here?
            if user_attributes != turn_result.user_attributes:
                self.user_table.persist(turn_result.user_attributes)
            self.state_table.persist(turn_result.current_state) # how do we get state?

        except:
            logger.error("Error persisting state")

        if self.new_session:
            self.new_session = False

        self.last_state_creation_time = current_state['creation_date_time']
        deserialized_current_state = {k: jsonpickle.decode(v) for k, v in turn_result.current_state.items()}

        return response, deserialized_current_state


def lambda_handler():
    local_agent = LocalAgent()
    user_input = ""
    while user_input != "bye":
        user_input = input()
        response, deserialized_current_state = local_agent.process_utterance(user_input)
        print(response)
