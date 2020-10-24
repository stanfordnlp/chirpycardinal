import logging
import time
import os
import sys
import warnings
from unittest import TestCase
from colorama import Fore
logging.getLogger("asyncio").setLevel(logging.ERROR)
logger = logging.getLogger('chirpylogger')
from copy import deepcopy

CHIRPY_HOME = os.environ.get('CHIRPY_HOME', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#CONFIG_FILE = os.environ.get('CONFIG_FILE', os.path.join(CHIRPY_HOME, 'bin/chirpy_cardinal_dev_service_config.json'))
#CONFIG_FILE = os.environ.get('CONFIG_FILE', os.path.join(CHIRPY_HOME, 'bin/chirpy_cardinal_beta_service_config.json'))
CONFIG_FILE = os.environ.get('CONFIG_FILE', os.path.join(CHIRPY_HOME, 'bin/chirpy_cardinal_mainline_service_config.json'))
sys.path = [CHIRPY_HOME]+sys.path
from bin.run_utils import setup_lambda, ASKInvocation, setup_logtofile
from chirpy.core.logging_formatting import colored
from chirpy.core.logging_utils import LoggerSettings, setup_logger


# Logging settings
# LOG_LEVEL sets the level for logging to screen and logging to file. When we run tests with nosetests, LOG_LEVEL sets
# the level of the logs shown for failed tests. See the "integration tests" internal documentation for more info.
LOG_LEVEL = logging.INFO
LOGTOSCREEN_USECOLOR = True  # turn off if you don't want color coded logging
PRINT_UTTERANCES = True  # whether to print the bot and user utterances as the tests are running

# Setup logging with integration test logger settings
log_directory, logtofile_path, _ = setup_logtofile('integration_test')
logger_settings = LoggerSettings(logtoscreen_level=LOG_LEVEL, logtoscreen_usecolor=LOGTOSCREEN_USECOLOR,
                                 logtofile_level=LOG_LEVEL, logtofile_path=logtofile_path,
                                 logtoscreen_allow_multiline=True, integ_test=True, remove_root_handlers=False)
setup_logger(logger_settings)


module_manager, lambda_fn = setup_lambda(lambda_fn_name='lambda_main', lambda_module_path='agent.agents.alexa.alexa_agent', service_config_file=CONFIG_FILE)

module_manager.start(CHIRPY_HOME)


def print_utterance(text):
    if PRINT_UTTERANCES:
        print(colored(text, fore=Fore.BLUE if LOGTOSCREEN_USECOLOR else None))

class BaseIntegrationTest(TestCase):

    #Following are experimental class attributes for testing in parallel using nosetests. Guidance on it coming soon
    #_multiprocess_can_split_ = True
    _multiprocess_shared_ = True

    #Default launch sequence, meant to be overriden by inheriting classes
    launch_sequence = ['let\'s chat']

    @classmethod
    def setUpClass(cls) -> None:
        """
        This method is run once for each of the class's objects (inlcuding objects of inheriting classes)
        It runs the launch sequence as defined in launch_sequence (which can be overriden by inheriting classes),
        saves the resulting AskInvocation object (which contains session_id and attributes) in base_ask
        :return:
        """
        warnings.filterwarnings("ignore", category=ResourceWarning, message="unclosed.*<ssl.SSLSocket.*>")
        base_test = cls()
        base_test.execute_launch_sequence()
        cls.base_ask = deepcopy(base_test.ask)
        cls.launch_responses = base_test.launch_responses

    def execute_launch_sequence(self):
        print(f"{self.id()}: Executing launch sequence ")
        self.launch_responses = []
        _, _, response_text = self.init_and_first_turn(launch_utterance=self.launch_sequence[0])
        self.launch_responses.append(response_text)
        for utt in  self.launch_sequence[1:]:
            _, _, response_text = self.process_utterance(utt)
            self.launch_responses.append(response_text)


    def setUp(self):
        """
        This functioon is called before every test function is executed.
        Since it calls reset_ask_to_post_launch_sequence, the default starting point for every test is after the
        launch sequence. It is possible to override this behaviour by calling init_and_first_turn within the test.
        :return:
        """
        super().setUp()
        self.reset_ask_to_post_launch_sequence()
        self.startTime = time.time()

    def reset_ask_to_post_launch_sequence(self):
        """
        Creates a deepcopy of base_ask and saves it in self.ask. Can also be used to reset self.ask within a test
        (such as when looping within a single test over different testing parameters)

        Working -
        1) the session_id and attributes (which includes state's creation_date_time) from base_ask are transferred to this object.
        2) when the process_utterance function is called, the session_id and state's creation_date_time are
        used to create the new event object.
        3) The lambda function then which then retrieves the state using the provided session_id and creation_date_time
        which corresponds to the state saved right after the launch sequence
        :return:
        """
        print(f"{self.id()}: Resetting to end of launch sequence")
        if not hasattr(self, 'base_ask'):
            self.execute_launch_sequence()
            self.base_ask = deepcopy(self.ask)
        else:
            self.ask = deepcopy(self.base_ask)
        for user_utterance, bot_utterance in zip(self.launch_sequence, self.launch_responses):
            print_utterance('User utterance: {}'.format(user_utterance))
            print_utterance('Bot utterance: {}'.format(bot_utterance))
        print(f"{self.id()}: Starting test sequence")

    def init_and_first_turn(self, launch_utterance="let's chat"):
        """Creates a new ASK Invocation"""
        self.ask = ASKInvocation(lambda_fn, 'integration_test')
        print_utterance('\nUser launch phrase: {}'.format(launch_utterance))
        alexa_response, current_state = self.ask.open_skill(launch_utterance)
        response_text = self.ask.clean_ssml(alexa_response['response']['outputSpeech']['ssml'])
        print_utterance('Bot utterance: {}'.format(response_text))
        return alexa_response, current_state, response_text

    def process_utterance(self, utterance, test_args=None):
        print_utterance('User utterance: {}'.format(utterance))
        if test_args:
            print('Test Args: {}'.format(test_args))
        alexa_response, current_state = self.ask.process(utterance, test_args=test_args)
        response_text = self.ask.clean_ssml(alexa_response['response']['outputSpeech']['ssml'])
        module_manager.log(log_directory)
        print_utterance('Bot utterance: {}'.format(response_text))
        return alexa_response, current_state, response_text

    def tearDown(self):
        t = time.time() - self.startTime
        print('%s: took %.3f seconds' % (self.id(), t))





