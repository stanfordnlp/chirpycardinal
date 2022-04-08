from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, ResponsePriority
from chirpy.response_generators.launch.state import ConditionalState, State
from chirpy.core.response_generator.treelet import Treelet

import os

# so we can instantly tell if it's a dev conversation (:p)
LAUNCH_PHRASE_MAINLINE = "Hi, this is an Alexa Prize Socialbot. I'd love to get to know you a bit better before we chat! Is it all right if I ask for your name?"
LAUNCH_PHRASE_DEV = "Hi, this is an Alexa Prize Socialbot. I'd like to get to know you a bit better before we chat! Is it all right if I ask for your name?"


class FirstTurnTreelet(Treelet):
    name = "launch_first_turn_treelet"

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        pipeline = os.environ.get('PIPELINE')
        user_name = self.rg.get_user_attribute('name', None)
        if user_name is not None:
            launch_phrase = f"Hi, this is an Alexa Prize Socialbot. I believe we may have met before. Are you {user_name}?"
            return ResponseGeneratorResult(text=launch_phrase, priority=priority, needs_prompt=False,
                                           state=state, cur_entity=None,
                                           conditional_state=ConditionalState(
                                               prev_treelet_str=self.name,
                                               next_treelet_str=self.rg.recognized_name_treelet.name)
                                           )
        else:
            launch_phrase = LAUNCH_PHRASE_MAINLINE if pipeline == 'MAINLINE' else LAUNCH_PHRASE_DEV

            return ResponseGeneratorResult(text=launch_phrase, priority=priority, needs_prompt=False,
                                           state=state, cur_entity=None,
                                           conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                                              next_treelet_str=self.rg.handle_name_treelet.name)
                                           )
