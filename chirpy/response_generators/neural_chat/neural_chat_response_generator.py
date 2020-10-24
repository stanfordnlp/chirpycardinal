from typing import Optional
import logging
import random

from chirpy.core.callables import ResponseGenerator
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, emptyResult, PromptResult, emptyPrompt, PromptType, UpdateEntity
from chirpy.response_generators.neural_chat.state import State, ConditionalState
from chirpy.response_generators.neural_chat.treelets.currentandrecentactivities_treelet import CurrentAndRecentActivitiesTreelet
from chirpy.response_generators.neural_chat.treelets.futureactivities_treelet import FutureActivitiesTreelet
from chirpy.response_generators.neural_chat.treelets.generalactivities_treelet import GeneralActivitiesTreelet
from chirpy.response_generators.neural_chat.treelets.emotions.emotions_treelet import EmotionsTreelet
from chirpy.response_generators.neural_chat.treelets.livingsituation_treelet import LivingSituationTreelet
from chirpy.response_generators.neural_chat.treelets.food_treelet import FoodTreelet
from chirpy.response_generators.neural_chat.treelets.familymember_treelets.familymember_treelets import OlderFamilyMembersTreelet, FriendsTreelet, SiblingsCousinsTreelet, PetsTreelet, KidsTreelet, PartnersTreelet
from chirpy.core.smooth_handoffs import SmoothHandoff


logger = logging.getLogger('chirpylogger')

# dict mapping name (str) to Treelet class
NAME2TREELET = {treelet.__name__: treelet for treelet in [CurrentAndRecentActivitiesTreelet, FutureActivitiesTreelet,
                                                          GeneralActivitiesTreelet, EmotionsTreelet,
                                                          LivingSituationTreelet, FoodTreelet,
                                                          OlderFamilyMembersTreelet, FriendsTreelet,
                                                          SiblingsCousinsTreelet,
                                                          PetsTreelet, KidsTreelet, PartnersTreelet]}

def get_test_args_treelet(current_state) -> Optional[str]:
    """If TestArgs specify a neural chat treelet, return it. Otherwise return None."""
    if hasattr(current_state, 'test_args') and \
        hasattr(current_state.test_args, 'neural_chat_args') and \
            'treelet' in current_state.test_args.neural_chat_args:
                test_args_treelet = current_state.test_args.neural_chat_args['treelet']
                return test_args_treelet
    return None


def choose_treelet_result(treeletname2result, current_state):
    """If a treelet is specified in test_args, choose that, otherwise randomly sample"""
    test_args_treelet = get_test_args_treelet(current_state)
    if test_args_treelet:
        sampled_treelet_name = test_args_treelet
        logger.primary_info(f'According to test args, choosing {test_args_treelet} instead of randomly sampling')
    else:
        sampled_treelet_name = random.choice(list(treeletname2result.keys()))
        logger.primary_info(f'Sampled treelet {sampled_treelet_name} from these: {treeletname2result.keys()}')
    sampled_response = treeletname2result[sampled_treelet_name]
    return sampled_response


class NeuralChatResponseGenerator(ResponseGenerator):
    """
    This RG uses GPT2ED to generate responses.
    Currently, it just does the "how was your day" conversation
    """
    name='NEURAL_CHAT'
    def init_state(self) -> State:
        state = State()
        logger.debug(f"Created neuralchat state: {state}")
        return state

    def get_response(self, state: State) -> ResponseGeneratorResult:

        # Init all treelets
        name2initializedtreelet = {treelet_name: treelet_class(self) for treelet_name, treelet_class in NAME2TREELET.items()}

        # Run update_state for all treelets
        for treelet in name2initializedtreelet.values():
            treelet.update_state(state)

        # If there is a next treelet to run, get response from it
        if state.next_treelet is not None:
            next_treelet = name2initializedtreelet[state.next_treelet]  # initialized treelet
            logger.primary_info(f'Continuing GPT2ED conversation in {state.next_treelet}')
            return next_treelet.get_response(state)

        # If any unused treelet has a starter question response, give it
        unused_treelet_names = [treelet_name for treelet_name in name2initializedtreelet if not state.treelet_has_been_used(treelet_name)]  # list of treelet names
        logger.primary_info(f'Getting starter question responses from these unused treelets: {unused_treelet_names}')
        treeletname2responseresult = {treelet_name: name2initializedtreelet[treelet_name].get_starter_question_response(state) for treelet_name in unused_treelet_names}
        treeletname2responseresult = {treelet_name: response_result for treelet_name, response_result in treeletname2responseresult.items() if response_result is not None}
        logger.primary_info("Got these starter questions from neural chat treelets:\n{}".format('\n'.join([f"{treelet_name}: {response_result}" for treelet_name, response_result in treeletname2responseresult.items()])))
        if treeletname2responseresult:
            top_priority = max([response_result.priority for response_result in treeletname2responseresult.values()])
            treeletname2responseresult = {treelet_name: response_result for treelet_name, response_result in treeletname2responseresult.items() if response_result.priority == top_priority}
            logger.primary_info(f"Restricting to just these results with top_priority={top_priority.name}: {treeletname2responseresult.keys()}")
            sampled_response = choose_treelet_result(treeletname2responseresult, self.state_manager.current_state)
            return sampled_response

        return emptyResult(state)


    def get_launch_prompt(self, name2initializedtreelet, state) -> Optional[PromptResult]:
        """Get a starter question prompt to be used as part of launch sequence"""
        treeletname2launchprompt = {treelet_name: treelet.get_prompt(state, for_launch=True) for treelet_name, treelet in name2initializedtreelet.items() if treelet.launch_appropriate}
        logger.primary_info("LAUNCH is doing smooth handoff to NEURAL_CHAT. Got these launch-appropriate starter questions:\n{}".format('\n'.join([f"{treelet_name}: {prompt_result}" for treelet_name, prompt_result in treeletname2launchprompt.items()])))
        treeletname2launchprompt = {treelet_name: prompt_result for treelet_name, prompt_result in treeletname2launchprompt.items() if prompt_result is not None}
        if not treeletname2launchprompt:
            logger.error(f'LAUNCH is doing smooth handoff to NEURAL_CHAT, but no launch treelets are appropriate')
            return None
        else:
            prompt_result = choose_treelet_result(treeletname2launchprompt, self.state_manager.current_state)
            prompt_result.type = PromptType.FORCE_START
            return prompt_result


    def get_prompt(self, state: State) -> PromptResult:

        # Init all treelets
        name2initializedtreelet = {treelet_name: treelet_class(self) for treelet_name, treelet_class in NAME2TREELET.items()}

        # Complete a smooth handoff if required
        if self.state_manager.current_state.smooth_handoff == SmoothHandoff.LAUNCH_TO_NEURALCHAT:
            launch_prompt_result = self.get_launch_prompt(name2initializedtreelet, state)
            if launch_prompt_result:
                return launch_prompt_result

        # Otherwise, get starter question prompts from all unused treelets
        unused_treelet_names = [treelet_name for treelet_name in name2initializedtreelet if not state.treelet_has_been_used(treelet_name)]  # list of treelet names
        logger.primary_info(f'Getting starter question prompts from these unused treelets:\n{unused_treelet_names}')
        treeletname2promptresult = {treelet_name: name2initializedtreelet[treelet_name].get_prompt(state) for treelet_name in unused_treelet_names}
        treeletname2promptresult = {treelet_name: prompt_result for treelet_name, prompt_result in treeletname2promptresult.items() if prompt_result is not None}
        logger.primary_info("Got these starter questions from neural chat treelets:\n{}".format('\n'.join([f"{treelet_name}: {prompt_result}" for treelet_name, prompt_result in treeletname2promptresult.items()])))

        # Sample one of highest priority and return
        if treeletname2promptresult:
            top_priority = max([prompt_result.type for prompt_result in treeletname2promptresult.values()])
            treeletname2promptresult = {treelet_name: prompt_result for treelet_name, prompt_result in treeletname2promptresult.items() if prompt_result.type==top_priority}
            logger.primary_info(f"Restricting to just these results with top_priority={top_priority.name}: {treeletname2promptresult.keys()}")

            # If a treelet is specified by test args, choose that. Otherwise randomly sample.
            sampled_prompt = choose_treelet_result(treeletname2promptresult, self.state_manager.current_state)
            return sampled_prompt
        else:
            logger.primary_info(f'Neural Chat has no more unused treelets left, so giving no prompt')
            return emptyPrompt(state)


    def update_state_if_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        assert conditional_state is not None, "conditional_state shouldn't be None if the response/prompt was chosen"
        state.update_if_chosen(conditional_state)
        return state


    def update_state_if_not_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        if conditional_state is not None:
            state.update_if_not_chosen(conditional_state)
        return state


    def get_entity(self, state: State) -> UpdateEntity:
        return UpdateEntity(False)