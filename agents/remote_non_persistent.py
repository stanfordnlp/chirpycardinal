import os
import argparse
import sys
sys.path.append('..')

from chirpy.core.logging_utils import setup_logger, PROD_LOGGER_SETTINGS

import logging

from agents.local_agent import LocalAgent
from chirpy.core import flags

#from chirpy.response_generators.red_question_response_generator import RedQuestionResponseGenerator


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
    test_script = ["", "em", "i like fried rice", "i like to add bacon", "really?", "i didn't know that"]
    local_agent = RemoteNonPersistentAgent('a', 'b', False, 0)
    user_input = ""
    while user_input != "bye":
        if len(test_script):
            user_input = test_script[0]
            test_script.pop(0)
            print('>', user_input)
        else:
            user_input = input('> ')
        response, deserialized_current_state = local_agent.process_utterance(user_input)
        print(response)

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Process what retrieval mechanism we will use"
    )
    parser.add_argument('--use_colbert', action = 'store_true', default = False)
    return parser

if __name__ == '__main__':
    parser = init_argparse()
    args = parser.parse_args()

    remote_url_config = {
        "corenlp": {
            "url": "http://localhost:4080"
        },
        "dialogact": {
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
        "convpara": {
            "url": "http://localhost:4085"
        },
        "entitylinker": {
            "url": "http://localhost:4086"
        },
        "blenderbot": {
            "url": "http://localhost:4087"
        },
        "responseranker": {
            "url": "http://localhost:4088"
        },
        "stanfordnlp": {
            "url": "http://localhost:4089"
        },
        "infiller": {
            "url": "WILL HARDCODE THIS" # TODO (eric): REPLACE THIS WITH SOMETHING MEANINGFUL
        } if args.use_colbert else { # chirpy2022 project
            "url": "http://localhost:4090"
        }
    }

    # initializing environment variables for the session based off of remote config urls
    for callable, config in remote_url_config.items():
        os.environ[f'{callable}_URL'] = config['url']

    if args.use_colbert:
        os.environ['usecolbert'] = True

    os.environ['ES_PORT'] = '443'
    os.environ['ES_SCHEME'] = 'https'

    lambda_handler()
