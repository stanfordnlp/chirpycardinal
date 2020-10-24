from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyPrompt, ResponsePriority
from chirpy.response_generators.launch.launch_utils import ConditionalState, State
from chirpy.response_generators.launch.launch_utils import Treelet
from chirpy.response_generators.launch.treelets.handle_name_treelet import HandleNameTreelet


LAUNCH_PHRASE = "Hi, this is an Alexa Prize Socialbot. I'd love to get to know you a bit better before we chat! Is it all right if I ask for your name?"

class FirstTurnTreelet(Treelet):

    def get_response(self, state: State) -> ResponseGeneratorResult:

        # If the user's name is already set in user_attributes, wipe it so we start fresh (this avoids problems if e.g.
        # Alice talks to our bot and gives their name, then Bob talks to our bot and refuses to tell us their
        # name, then we might refer to Bob as Alice in the second conversation).
        # In the future we may want to support greeting users by remembered name, but until then let's do this
        setattr(self.state_manager.user_attributes, 'name', None)

        return ResponseGeneratorResult(text=LAUNCH_PHRASE, priority=ResponsePriority.FORCE_START, needs_prompt=False,
                                       state=state, cur_entity=None,
                                       conditional_state=ConditionalState(HandleNameTreelet.__name__))

    def get_prompt(self, state: State) -> PromptResult:
        return emptyPrompt(state)