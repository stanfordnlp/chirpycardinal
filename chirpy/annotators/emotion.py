import logging

from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager

logger = logging.getLogger('chirpylogger')

MAX_HISTORY_SIZE = 2  # how many previous utterances to use. Includes both bot and user utterances. Doesn't include user's current utterance

#For reference
EMOTIONS = set(['grateful', 'ashamed', 'nostalgic', 'hopeful', 'anticipating', 'impressed', 'furious', 'sad', 'jealous',
 'annoyed', 'embarrassed', 'excited', 'content', 'caring', 'guilty', 'faithful', 'afraid', 'proud', 'prepared',
 'devastated', 'disappointed', 'lonely', 'confident', 'sentimental', 'joyful', 'anxious', 'terrified', 'trusting',
 'angry', 'apprehensive', 'disgusted', 'surprised'])

class EmotionAnnotator(Annotator):
    name='user_emotion'
    def __init__(self, state_manager: StateManager, timeout=1.5, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data=None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        return None

    def execute(self, input_data=None):
        """
        Run emotion classifier on input_data and return an emotion label.
        The emotion classifier is trained on Empathetic Dialogues Dataset (https://arxiv.org/abs/1811.00207)
        to predict the emotion given an utterance

        Args:
            input_data (dict): With keys
                "utterance": Input to emotion classifier

        Returns:
            str: emotion label for the utterance (from the list of EMOTIONS)
        """
        user_utterance = self.state_manager.current_state.text
        if input_data is None:
            input_data = {'utterance': user_utterance}

        if not input_data['utterance']:
            return self.get_default_response()

        # Replace , with _comma_ as that was the input data to classifier. Needs to be changed back in the future when
        # the classifier is retrained with ,
        user_utterance = user_utterance.replace(',', '_comma_')

        # NOTE: Errors thrown (including ones for timeouts) are not caught here. They should be caught by the caller.
        # Don't return default response here. That will be handled by save_and_execute.
        # Just catch new errors and throw them, or return the result
        # All the error logging should happen here
        logger.debug(f'Calling Emotion Classifier Remote module with utterance="{user_utterance}"')
        output = super().execute(input_data)
        if output is None:
            default_response = self.get_default_response()
            logger.info(f'{type(self).__name__} using default response: {default_response}')
            return default_response
        # TODO: Change this to not assume the return type is a list, before pushing to dev
        emotion = output['response']
        assert emotion in EMOTIONS
        logger.debug(f'User emotion classified as "{emotion}"')
        return emotion
