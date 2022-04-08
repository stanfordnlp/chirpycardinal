import logging

# RG IMPORTS
from chirpy.core.response_generator import Treelet
from chirpy.response_generators.aliens.aliens_responses import PROMPT
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType

logger = logging.getLogger('chirpylogger')


class IntroductoryTreelet(Treelet):
    name = 'aliens_introductory'

    def get_prompt(self, **kwargs):
        discussed_aliens_in_prev_convo = self.rg.get_user_attribute('discussed_aliens', False)
        state = self.rg.state
        num_convo_turns = len(self.rg.get_conversation_history()) // 2
        if state.have_prompted or num_convo_turns <= 30 or discussed_aliens_in_prev_convo:
            return None # don't prompt for aliens more than once

        return PromptResult(
            PROMPT,
            PromptType.FORCE_START,
            state,
            cur_entity=None,
            conditional_state=self.rg.ConditionalState(
                have_prompted=True,
                prev_treelet_str=self.name,
                next_treelet_str='transition'
            )
        )

