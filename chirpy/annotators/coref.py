import logging

from chirpy.core.callables import Annotator
from chirpy.core.state_manager import StateManager

logger = logging.getLogger('chirpylogger')

MAX_HISTORY_SIZE = 2  # how many previous utterances to use. Includes both bot and user utterances. Doesn't include user's current utterance

class CorefAnnotator(Annotator):
    name='coref'
    def __init__(self, state_manager: StateManager, timeout=1, url=None, input_annotations = []):
        super().__init__(state_manager=state_manager, timeout=timeout, url=url, input_annotations=input_annotations)

    def get_default_response(self, input_data=None):
        """The default response to be returned in case this module's execute fails, times out or is cancelled"""
        if input_data:
            return {'coref_resolved_user_utterance': input_data['utterance'], 'coref_clusters': {}}
        else:
            user_utterance = self.state_manager.current_state.text
            return {'coref_resolved_user_utterance': user_utterance, 'coref_clusters': {}}

    def execute(self, input_data=None):
        """
        Execute SpaCy/Huggingface implementation of Kevin's Neural Coref on input_data.

        Args:
            input_data (dict): With keys:
                "context" : the text before utterance that can be used to resolve coref
                "utterance" : the text to be resolved
                When this argument isn't provided it uses the current user utterance as "utterance"
                and past MAX_HISTORY_SIZE turns as "context"

        Returns:
            Dict: With keys
                "coref_resolved_user_utterance": user utterance with third person pronouns resolved to canonical mentions
                "coref clusters": Dictionary with canonical mentions as and list of coreferant mentions as values

        """
        user_utterance = self.state_manager.current_state.text
        history = self.state_manager.current_state.history
        context = ' '.join(history[-MAX_HISTORY_SIZE:]) or ''
        if input_data is None:
            input_data = {'context': context, 'utterance': user_utterance}
        # NOTE: Errors thrown (including ones for timeouts) are not caught here. They should be caught by the caller.
        # Don't return default response here. That will be handled by save_and_execute.
        # Just catch new errors and throw them, or return the result
        # All the error logging should happen here
        if len(history) == 0:
            logger.info("No history to decontextualize, returning the original unchanged utterance")
            return self.get_default_response()

        logger.debug(f'Resolving Coref with context="{context}" and utterance="{user_utterance}"')
        coref_output = self.remote_call(input_data)
        if coref_output is None:
            default_response = self.get_default_response()
            logger.info(f'{type(self).__name__} using default response: {default_response}')
            return default_response
        coref_resolved_user_utterance = coref_output['resolved']
        coref_clusters = coref_output['clusters']

        logger.debug(f'Coref resolved user utterance to "{coref_resolved_user_utterance}"')
        return {'coref_resolved_user_utterance': coref_resolved_user_utterance, 'coref_clusters': coref_clusters}
