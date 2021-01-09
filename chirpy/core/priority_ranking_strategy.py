import logging
from typing import Dict, Optional
from chirpy.core.response_priority import ResponsePriority, PromptType, TiebreakPriority, PROMPT_TYPE_DIST, PROMPT_DISTS_OVER_RGS
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.core.state_manager import StateManager
from collections import OrderedDict
from random import shuffle
from chirpy.core.util import sample_from_prob_dist_dict, normalize_dist
from chirpy.core.test_args import TestArgs


logger = logging.getLogger('chirpylogger')


class RankedResults(OrderedDict):
    """
    A class to represent a dictionary of results, mapping from RG name (string) to RG result (ResponseGeneratorResult
    or PromptResult), that is sorted by descending priority.
    """

    @property
    def top_rg(self) -> str:
        top_rg, top_result = list(self.items())[0]
        return top_rg

    @property
    def top_result(self):  # returns a ResponseGeneratorResult or PromptResult
        top_rg, top_result = list(self.items())[0]
        return top_result

    def remove_result(self, rg):
        """Remove the key/val pair with key=rg. Logs if this means the top result has changed."""
        removing_top = (rg == self.top_rg)
        if removing_top:
            old_top_rg = rg
            old_top_response = self[rg]
        del self[rg]
        if removing_top:
            logger.primary_info('Removed previous top result from RankedResults: {}={}\nNew top result: {}={}'.format(
                old_top_rg, old_top_response, self.top_rg, self.top_result), extra={'color_lines_by_component': True})


class PriorityRankingStrategy():
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.timeout_in_millis = 1000  # default timeout
        self.test_args = None

    def save_test_args(self, test_args: TestArgs):
        """
        Saves the test_args, so they can be used to select the prompt.
        """
        self.test_args = test_args

    def assign_tiebreak_priorities(self, results: Dict[str, ResponseGeneratorResult]):
        """
        Given responses that have the SAME ResponsePriority, assign each one a tiebreak_priority.
        This will be used to break ties among this group (but will have no effect outside this group).

        Inputs:
            results: non-empty dict from rg name to ResponseGeneratorResult (all with same priority).

        Result: each ResponseGeneratorResult in results now has a tiebreak_priority (int). The numbers
            themselves aren't important, only the relative ordering within this group.
        """
        # Check they all have the same priority
        group_priority = list(results.values())[0].priority
        assert all([result.priority == group_priority for result in results.values()])
#
        # Default behavior is to use the RG ordering given in TiebreakPriority
        for rg, result in results.items():
            result.tiebreak_priority = TiebreakPriority[rg].value

        # On first turn, LAUNCH should have highest tiebreak_priority because we *must* begin each conversation with
        # "Hi, this is an Alexa Prize Socialbot". Even if the user's launch phrase was offensive or a red question,
        # LAUNCH should win the tiebreak against OFFENSIVE_USER and RED_QUESTION.
        if self.state_manager.last_state is None:
            if 'LAUNCH' in results:
                results['LAUNCH'].tiebreak_priority = max([result.tiebreak_priority for result in results.values()]) + 1

        # Log
        rgs_by_tiebreak_pri = sorted(results.keys(), key=lambda rg: results[rg].tiebreak_priority, reverse=True)
        logger.info('For {}={}, assigned tiebreak priorities: {}'.format(
            type(group_priority).__name__, group_priority.name,
            ", ".join(["{}: {}".format(rg, results[rg].tiebreak_priority) for rg in rgs_by_tiebreak_pri])
        ))

    def rank_responses(self, responses: Dict[str, ResponseGeneratorResult]):
        """
        Sort the responses by priority.

        :param responses: dict from rg name to its corresponding ResponseGeneratorResult
        :return: RankedResults. Same as responses but sorted by descending priority
        """
        if 'FALLBACK' not in responses:
            logger.error('Running priority ranking strategy on responses, but FALLBACK is not in responses', stack_info=True)

        # Within groups of responses that have the same ResponsePriority, assign tiebreak_priorities
        for priority in ResponsePriority:
            priority_group = {rg: response for rg, response in responses.items() if response.priority == priority}
            if priority_group:
                self.assign_tiebreak_priorities(priority_group)

        # priority_sorted_responses is a list of (rg_name, ResponseGeneratorResult) pairs
        # sorted by descending ResponsePriority, with ties broken by tiebreak_priority
        priority_sorted_responses = sorted(responses.items(),
                                           key=lambda rg_and_response: (rg_and_response[1].priority,
                                                                        rg_and_response[1].tiebreak_priority),
                                           reverse=True)
        return RankedResults(priority_sorted_responses)


    def rank_prompts(self, prompts: Dict[str, PromptResult], turns_since_last_active : Optional[Dict[str, int]]):
        """
        Samples a prompt type from the available prompt types according to PROMPT_TYPE_DIST, then samples a RG from the
        RGs that gave a prompt of that type using PROMPT_DISTS_OVER_RGS. Puts this #1 prompt first, then all other
        non-NO prompts in a random order.

        :param prompts: dict from rg name to its corresponding PromptResult
        :return: RankedResults. Same as prompts but sorted by descending priority
        """
        if 'FALLBACK' not in prompts:
            logger.error('Running priority ranking strategy on prompts, but FALLBACK is not in prompts', stack_info=True)

        # Identify which RGs gave no prompt
        no_rgs = {rg for rg, prompt_result in prompts.items() if prompt_result.type == PromptType.NO}

        selected_rg = None

        # If self.test_args.selected_prompt_rg gave a prompt this turn, choose that
        if self.test_args and self.test_args.selected_prompt_rg:
            if self.test_args.selected_prompt_rg not in prompts:
                logger.warning(f"In TestArgs, selected_prompt_rg='{self.test_args.selected_prompt_rg}', but that RG does not have a prompt in prompts. Proceeding as if no testargs were given.")
            elif self.test_args.selected_prompt_rg in no_rgs:
                logger.warning(f"In TestArgs, selected_prompt_rg='{self.test_args.selected_prompt_rg}', but that RG gave a prompt with type='{PromptType.NO.name}'. Proceeding as if no testargs were given.")
            else:
                selected_rg = self.test_args.selected_prompt_rg
                logger.primary_info(f"Due to TestArgs, priority sampling strategy chose the {prompts[selected_rg].type.name} prompt from {selected_rg}")

        # Otherwise:
        if selected_rg is None:
            # Get the probdist over prompt types, normalized for the available types on this turn
            available_prompt_types = {prompt_result.type for prompt_result in prompts.values() if prompt_result.type!=PromptType.NO}
            prompt_type_dist = {prompt_type: PROMPT_TYPE_DIST[prompt_type] for prompt_type in available_prompt_types}
            prompt_type_dist = normalize_dist(prompt_type_dist)
            for prompt_type, val in prompt_type_dist.items():
                if val == 0:
                    logger.warning(f'There are some prompts of type {prompt_type.name} on this turn, but that type has zero probability in prompt_type_dist.')

            # Sample a prompt type
            selected_prompt_type = sample_from_prob_dist_dict(prompt_type_dist)
            logger.primary_info(f"Priority sampling strategy sampled prompt type {selected_prompt_type.name} from this distribution of available types: {prompt_type_dist}")

            # Get the probdist for RGs of selected_prompt_type, normalized for the available RGs on this turn
            rgs_dist = {}
            for rg in {rg for rg, prompt_result in prompts.items() if prompt_result.type == selected_prompt_type}:
                if rg not in PROMPT_DISTS_OVER_RGS[selected_prompt_type]:
                    logger.error(f"{rg} gave a prompt of type {selected_prompt_type.name} but {rg} is not in the RG_dist for that type")
                    continue
                val = PROMPT_DISTS_OVER_RGS[selected_prompt_type][rg]
                if val == 0:
                    logger.error(f"{rg} gave a prompt of type {selected_prompt_type.name} but {rg} has probability 0 in the distribution for that type. If this is not intended, the probability should be raised.")
                rgs_dist[rg] = val
            rgs_dist = normalize_dist(rgs_dist)

            # Re-weight the distribution over RGs according to when those RGs were last active
            try:
                if turns_since_last_active is not None:
                    reweighted_rgs_dist = {rg: weight * turns_since_last_active[rg] for rg, weight in rgs_dist.items()}
                    reweighted_rgs_dist = normalize_dist(reweighted_rgs_dist)
                    logger.primary_info(f"To select a prompt, we reweighted the rgs_dist according to turns_since_last_active={turns_since_last_active}:"
                                        f"\nOriginal:  {rgs_dist}\nReweighted:{reweighted_rgs_dist}")
                    rgs_dist = reweighted_rgs_dist
            except Exception as e:
                logger.error(f"Error in populating the turns_since_last_active field! Error is {e}")

            # Sample a RG
            selected_rg = sample_from_prob_dist_dict(rgs_dist)
            logger.primary_info(f"Priority sampling strategy sampled RG {selected_rg} from this distribution of RGs that gave prompts of type {selected_prompt_type.name}: {rgs_dist}")

        # Init results
        results = OrderedDict()

        # Add the selected prompt to results first
        results[selected_rg] = prompts[selected_rg]

        # Randomly select all other RGs that gave a prompt to be the next options
        next_rgs = [rg for rg, prompt in prompts.items() if prompt.type != PromptType.NO and rg != selected_rg]
        shuffle(next_rgs)
        for rg in next_rgs:
            results[rg] = prompts[rg]

        # Add remaining NO type prompts to results
        for rg in no_rgs:
            results[rg] = prompts[rg]

        return RankedResults(results)