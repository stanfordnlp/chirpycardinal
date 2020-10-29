"""
in main loop:

1. run remote modules
2. initialize text agent (run server)
3. enter loop in commandline and interact with text agent
"""
import os
import requests
import logging
from flask import Flask
from agent.agents.local.local_agent import LocalAgent
from chirpy.core.logging_utils import LoggerSettings, setup_logger
from local_callable_manager import LocalCallableManager

CHIRPY_HOME = os.environ.get('CHIRPY_HOME', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
app = Flask(__name__)

# Logging settings
LOGTOSCREEN_LEVEL = logging.INFO + 5
LOGTOFILE_LEVEL = logging.DEBUG

def init_logger():
    logger_settings = LoggerSettings(logtoscreen_level=LOGTOSCREEN_LEVEL, logtoscreen_usecolor=True,
                                     logtofile_level=LOGTOFILE_LEVEL, logtofile_path='',
                                     logtoscreen_allow_multiline=True, integ_test=False, remove_root_handlers=False)
    setup_logger(logger_settings)

def setup_callables():
    config_fname = os.path.join(CHIRPY_HOME, "bin/local_callable_config.json")
    callable_manager = LocalCallableManager(config_fname)
    callable_manager.start_containers()
    return callable_manager

def get_lambda_fn(lambda_handler_path):
    lambda_module = __import__(lambda_handler_path, fromlist=['lambda_handler'])
    return getattr(lambda_module, 'lambda_handler')

def main():
    init_logger()
    callable_manager = setup_callables() # check if container is already running
    lambda_handler_path = 'lambda_module'
    lambda_fn = get_lambda_fn(lambda_handler_path)
    # execute dialogue in loop
    local_agent = LocalAgent()
    should_end_conversation = False
    while not should_end_conversation:
        user_utterance = input("> ")
        response, should_end_conversation = lambda_fn(local_agent, user_utterance)
        print(response)

    callable_manager.stop_containers()
    
if __name__ == "__main__":
    main()