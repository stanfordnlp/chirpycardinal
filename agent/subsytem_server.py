import json
import uuid
import datetime
import logging
import jsonpickle
from flask import Flask, request, jsonify

from chirpy.response_generators.launch.launch_response_generator import LaunchResponseGenerator
from chirpy.response_generators.fallback_response_generator import FallbackResponseGenerator
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
from chirpy.core.logging_utils import LoggerSettings, setup_logger

from chirpy.annotators.corenlp import CorenlpModule
from chirpy.annotators.navigational_intent.navigational_intent import NavigationalIntentModule
from chirpy.annotators.stanfordnlp import StanfordnlpModule
from chirpy.annotators.coref import CorefAnnotator
from chirpy.annotators.emotion import EmotionAnnotator
from chirpy.annotators.g2p import NeuralGraphemeToPhoneme
from chirpy.annotators.gpt2ed import GPT2ED
from chirpy.annotators.question import QuestionAnnotator
import chirpy.core.flags as flags
from chirpy.core.util import get_function_version_to_display
from chirpy.annotators.dialogact import DialogActAnnotator
from chirpy.core.entity_linker.entity_linker import EntityLinkerModule

from chirpy.core.handler import Handler

app = Flask(__name__)

# Timeout for NLP Pipeline
NLP_PIPELINE_TIMEOUT = 3 if flags.use_timeouts else flags.inf_timeout  #seconds

# Logging settings
LOGTOSCREEN_LEVEL = logging.INFO + 5
LOGTOFILE_LEVEL = logging.DEBUG

def init_logger():
    logger_settings = LoggerSettings(logtoscreen_level=LOGTOSCREEN_LEVEL, logtoscreen_usecolor=True,
                                     logtofile_level=LOGTOFILE_LEVEL, logtofile_path='',
                                     logtoscreen_allow_multiline=True, integ_test=False, remove_root_handlers=False)
    setup_logger(logger_settings)

"""
Initialize chirpy state from request
"""
def init_current_state(request):
    state_attributes = {}
    state_attributes['text'] = request.json['utterance']
    state_attributes['session_id'] = request.json['session_id']
    state_attributes['creation_date_time'] = str(datetime.datetime.utcnow().isoformat())
    state_attributes = {k: jsonpickle.encode(v) for k, v in state_attributes.items()}
    return state_attributes

"""
Extract desired values from handler result
"""
def build_response_state(deserialized_current_state, response):
    selected_response_rg = deserialized_current_state['selected_response_rg']
    selected_prompt_rg = deserialized_current_state['selected_prompt_rg']

    current_state = {'selected_response_rg': selected_response_rg,
                     'selected_prompt_rg': selected_prompt_rg,
                     'response': response,
                     'response_priority': deserialized_current_state['response_generator_states'][selected_response_rg]['priority'],
                     'prompt_priority': deserialized_current_state['response_generator_states'][selected_prompt_rg]['priority']
                     }
    
    return current_state

@app.route('/process_utterance', methods=['GET'])
def process_utterance():

    # create handler (pass in RGs + annotators)
    handler = Handler(
        response_generator_classes = [LaunchResponseGenerator, ComplaintResponseGenerator, ClosingConfirmationResponseGenerator,
                                      OneTurnHackResponseGenerator, FallbackResponseGenerator, WikiResponseGenerator,
                                      OffensiveUserResponseGenerator, OpinionResponseGenerator2, AcknowledgmentResponseGenerator,
                                      NeuralChatResponseGenerator, CategoriesResponseGenerator, ClosingConfirmationResponseGenerator,
                                      MusicResponseGenerator],
            annotator_classes = [QuestionAnnotator, DialogActAnnotator, NavigationalIntentModule, StanfordnlpModule, CorenlpModule,
                                EntityLinkerModule, NeuralGraphemeToPhoneme],
            annotator_timeout = NLP_PIPELINE_TIMEOUT
    )
    
    # get user_id
    if request.user_id is None:
        user_id = uuid.uuid4().hex
    else: 
        user_id = request.user_id

    # get current_state and last_state from request
    state_attributes = init_current_state(request)
    user_attributes = {'user_id': user_id}
    last_state = request.json['last_state']

    # execute handler
    turn_result = handler.execute(state_attributes, user_attributes, last_state)
    deserialized_current_state = {k: jsonpickle.decode(v) for k, v in turn_result.current_state.items()}

    # extract values to return from state
    response = turn_result.response
    current_state = build_response_state(deserialized_current_state, response)

    output = {'user_attributes': {},
              'response': response,
              'current_state': current_state}
    
    return jsonify(output)

if __name__ == '__main__':
    init_logger()
    app.run(port='5000')