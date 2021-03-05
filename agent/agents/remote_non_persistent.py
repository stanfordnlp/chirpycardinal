from pathlib import Path
import functools
import json
import os

from chirpy.core.logging_utils import setup_logger, PROD_LOGGER_SETTINGS


import jsonpickle
import logging

from agent.agents.local.local_agent import LocalAgent
from chirpy.core import flags
from chirpy.core.handler import Handler

from chirpy.response_generators.launch.launch_response_generator import LaunchResponseGenerator
from chirpy.response_generators.fallback_response_generator import FallbackResponseGenerator
#from chirpy.response_generators.red_question_response_generator import RedQuestionResponseGenerator
from chirpy.response_generators.offensive_user.offensive_user_response_generator import OffensiveUserResponseGenerator
from chirpy.response_generators.wiki.wiki_response_generator import WikiResponseGenerator
from chirpy.response_generators.opinion2.opinion_response_generator import OpinionResponseGenerator2
from chirpy.response_generators.neural_chat.neural_chat_response_generator import NeuralChatResponseGenerator
from chirpy.response_generators.categories.categories_response_generator import CategoriesResponseGenerator
from chirpy.response_generators.one_turn_hack_response_generator import OneTurnHackResponseGenerator
from chirpy.response_generators.neural_fallback_response_generator import NeuralFallbackResponseGenerator
from chirpy.response_generators.closing_confirmation_response_generator import ClosingConfirmationResponseGenerator
from chirpy.response_generators.complaint_response_generator import ComplaintResponseGenerator
from chirpy.response_generators.acknowledgment.acknowledgment_response_generator import AcknowledgmentResponseGenerator
from chirpy.response_generators.music.music_response_generator import MusicResponseGenerator


from chirpy.annotators.corenlp import CorenlpModule
from chirpy.annotators.navigational_intent.navigational_intent import NavigationalIntentModule
from chirpy.annotators.stanfordnlp import StanfordnlpModule
from chirpy.annotators.g2p import NeuralGraphemeToPhoneme
from chirpy.annotators.question import QuestionAnnotator
from chirpy.annotators.dialogact import DialogActAnnotator
from chirpy.core.entity_linker.entity_linker import EntityLinkerModule
# Timeout at the highest level, as close as possible to 10 seconds. Do nothing after, just create an apologetic
# response and send it over
OVERALL_TIMEOUT = 9.75 if flags.use_timeouts else flags.inf_timeout  # seconds

# Timeout for final_response function. Set at 9.35 seconds to comfortably log the latencies
FINAL_RESPONSE_TIMEOUT = 9.35 if flags.use_timeouts else flags.inf_timeout  #seconds

# Timeout for progressive response
PROGRESSIVE_RESPONSE_TIMEOUT = 3 if flags.use_timeouts else flags.inf_timeout  #seconds

# Timeout for NLP Pipeline
NLP_PIPELINE_TIMEOUT = 3 if flags.use_timeouts else flags.inf_timeout  #seconds

logger = logging.getLogger('chirpylogger')
root_logger = logging.getLogger()
if not hasattr(root_logger, 'chirpy_handlers'):
    setup_logger(PROD_LOGGER_SETTINGS)

class RemoteNonPersistentAgent(LocalAgent):
    def __init__(self, session_id, user_id, new_session, last_state_creation_time):
        super().__init__()
        self.session_id = session_id
        self.user_id = user_id
        self.new_session = new_session
        self.last_state_creation_time = last_state_creation_time

def lambda_handler():
    local_agent = RemoteNonPersistentAgent()
    user_input = ""
    while user_input != "bye":
        user_input = input()
        response, deserialized_current_state = local_agent.process_utterance(user_input)
        print(response)

if __name__ == '__main__':
    remote_url_config = {
        "corenlp": {
            "url": "http://localhost:4080"
        },
        "dialog_act": {
            "url": "http://localhost:4081"
        },

        "g2p": {
            "url": "http://localhost:4082"
        },
        "gpt2ed": {
            "url": "http://localhost:4083"
        },
        "question": {
            "url": "http://localhost:4084"
        },
        "stanfordnlp": {
            "url": "http://localhost:4085"
        },
    }
    for callable, config in remote_url_config.items():
        os.environ[f'{callable}_URL'] = config['url']

    os.environ['ES_PORT'] = '443'
    os.environ['ES_SCHEME'] = 'https'

    lambda_handler()

