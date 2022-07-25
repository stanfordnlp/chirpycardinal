import copy
import logging
from typing import Dict, List, Optional

from chirpy.core.callables import run_multithreaded, ResponseGenerators
# from chirpy.core.offensive_speech_classifier import OffensiveSpeechClassifier
from chirpy.core.state_manager import StateManager
from chirpy.core.priority_ranking_strategy import PriorityRankingStrategy
from chirpy.core.flags import use_timeouts, inf_timeout
from chirpy.core.priority_ranking_strategy import RankedResults
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, UpdateEntity, CONTINUING_ANSWER_TYPES, is_killed
from chirpy.core.util import print_dict_linebyline, sentence_join
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.response_generators.closing_confirmation.closing_confirmation_response_generator import CLOSING_CONFIRMATION_STOP
from chirpy.core.latency import measure


logger = logging.getLogger('chirpylogger')


class DialogManager:
    # These timeouts are in seconds
    INIT_STATE_TIMEOUT = 1 if use_timeouts else inf_timeout
    GET_ENTITY_TIMEOUT = 1 if use_timeouts else inf_timeout
    GET_RESPONSE_TIMEOUT = 7 if use_timeouts else inf_timeout
    GET_PROMPT_TIMEOUT = 1 if use_timeouts else inf_timeout
    UPDATE_STATE_TIMEOUT = None  # timeout for update_state_if_chosen and update_state_if_not_chosen fns
    # OFFENSIVE_TIMEOUT = 2 if use_timeouts else inf_timeout

    def __init__(self,
                 state_manager: StateManager,
                 ranking_strategy: PriorityRankingStrategy,
                 response_generators: ResponseGenerators
                 # TODO add response_generators as constructor argument
                 ) -> None:
        self.state_manager = state_manager
        self.ranking_strategy = ranking_strategy
        # self.offensive_speech_classifier = OffensiveSpeechClassifier(timeout_in_millis=self.OFFENSIVE_TIMEOUT * 1000)
        self.response_generators = response_generators


    @measure
    def execute_turn(self) -> (str, str, bool):
        """
        Execute one turn of dialogue.

        Returns:
            utterance: string (cannot be empty or None). The full utterance from Alexa.
            should_end_session: bool. Currently this is always False, but we might want to change it in the future
                e.g. if the user is being persistently offensive, talking about topics we aren't able to deal with,
                or the conversation is going really badly.
        """

        should_end_session = False
        logger.primary_info('Current state:\n{}'.format(print_dict_linebyline(self.state_manager.current_state.__dict__)),
                            extra={'color_lines_by_component': True})
        self.init_rg_states()  # Get RG states from last turn (or on first turn, run RGs' init_state fns)

        # Update the entity tracker state using the entity linker results
        self.update_entity_tracker_state()  # Update entity tracker's state

        if not hasattr(self.state_manager.current_state, 'turns_since_last_active'):
            turns_since_last_active = {rg_name: 34 for rg_name in self.response_generators.name_to_class}
            setattr(self.state_manager.current_state, 'turns_since_last_active', turns_since_last_active)
        try:
            for rg_name in self.response_generators.name_to_class:
                self.state_manager.current_state.turns_since_last_active[rg_name] += 1
        except Exception as e:
            logger.error(f"Error in incrementing the turns_since_last_active field! Error is {e}")

        # save turns_since_last_active state in User Table. only start saving after initial launch phase verifies
        # whether we recognize the user
        if len(self.state_manager.current_state.history) >= 6:
            setattr(self.state_manager.user_attributes, 'turns_since_last_active',
                    self.state_manager.current_state.turns_since_last_active)

        # Get response (and possibly prompt)
        selected_response_rg, selected_response, selected_prompt_rg, selected_prompt = self.get_response_and_prompt()
        try:
            self.state_manager.current_state.turns_since_last_active[selected_response_rg] = 0
            if selected_prompt_rg is not None:
                self.state_manager.current_state.turns_since_last_active[selected_prompt_rg] = 0
        except Exception as e:
            logger.error(f"Error in populating the turns_since_last_active field! Error is {e}")

        # If selected_response_rg is 'CLOSING_CONFIRMATION' and the response is empty, stop immediately
        # NOTE: can't create a response with priority diff than NO if the text is None
        if selected_response_rg == 'CLOSING_CONFIRMATION' and selected_response.text == CLOSING_CONFIRMATION_STOP:
            return None, None, True

        # Record the final response and prompt RGs
        setattr(self.state_manager.current_state, 'selected_response_rg', selected_response_rg)
        setattr(self.state_manager.current_state, 'selected_prompt_rg', selected_prompt_rg)

        # Get the utterance
        if selected_prompt_rg is None:
            utterance = selected_response.text
        else:
            utterance = sentence_join(selected_response.text, selected_prompt.text)

        # Log final RG states
        logger.primary_info('Final RG states at the end of this turn:\n{}'.format(
            print_dict_linebyline(self.state_manager.current_state.response_generator_states)),
            extra={'color_lines_by_component': True})

        return utterance, should_end_session

    def update_entity_tracker_state(self):
        """
        If the last active RG's get_entity function has an updated entity, update the entity tracker's state with it
        Else update entity tracker's state using default logic in entity tracker
        """

        # Get update_entity_result from last_active_rg
        last_active_rg = self.state_manager.last_state_active_rg  # str or None
        if last_active_rg:
            last_active_rg_state = copy.copy(self.state_manager.current_state.response_generator_states[last_active_rg])
            update_entity_results: Dict[str, UpdateEntity] = self.response_generators.run_multithreaded(
                rg_names=[last_active_rg],
                function_name='get_entity',
                args_list=[[last_active_rg_state, ]],
                timeout=DialogManager.GET_ENTITY_TIMEOUT)
            if update_entity_results and last_active_rg in update_entity_results:
                update_entity_result = update_entity_results[last_active_rg]
            else:
                logger.warning(
                    f"Failed or timed out while to running {last_active_rg}.get_entity. "
                    f"Skipping the RGs update to entity tracker")
                update_entity_result = UpdateEntity(False)
        else:
            update_entity_result = UpdateEntity(False)

        # Update the entity tracker, using update_entity_result if it has update=True
        if update_entity_result.update:
            logger.primary_info(f"Ran last_active_rg={last_active_rg}'s get_entity() function. It returned "
                                f"{update_entity_result}, so using this to update the entity tracker state",
                                extra={'color_msg_by_component': last_active_rg})
            self.state_manager.current_state.entity_tracker.update_from_rg(update_entity_result, last_active_rg, self.state_manager.current_state)
        else:
            if last_active_rg is not None:
                logger.primary_info(f"Ran last_active_rg={last_active_rg}'s get_entity() function. It returned "
                                    f"{update_entity_result}, so the entity tracker will update its state in the normal way",
                                    extra={'color_msg_by_component': last_active_rg})
            self.state_manager.current_state.entity_tracker.update_from_user(self.state_manager)


    def get_response_and_prompt(self)  -> (str, ResponseGeneratorResult, Optional[str], Optional[PromptResult]):
        """
        Gets response and possibly prompt (both checked for offensiveness).

        Returns:
            selected_response_rg: string
            selected_response: ResponseGeneratorResult
            selected_prompt_rg: string or None
            selected_prompt: PromptResult or None
        """

        # Get responses from RGs, ranked by priority
        logger.primary_info(f'Getting responses from RGs...')
        ranked_responses = self.run_rgs_and_rank('response')

        # Check that the top response isn't offensive (and remove it if it is)
        ranked_responses = self.remove_offensive(ranked_responses)

        # Choose the top response
        selected_response, selected_response_rg = ranked_responses.top_result, ranked_responses.top_rg
        logger.primary_info(f'Selected response from {selected_response_rg}: {selected_response}',
                            extra={'color_msg_by_component': selected_response_rg})

        # If the responding RG gave a smooth_handoff identifier, put it in current_state
        setattr(self.state_manager.current_state, 'smooth_handoff', selected_response.smooth_handoff)
        if selected_response.smooth_handoff is not None:
            logger.primary_info(f"Setting current_state.smooth_handoff to {selected_response.smooth_handoff} provided "
                                f"by selected_response_rg={selected_response_rg}",
                                extra={'color_msg_by_component': selected_response_rg})

        # Update the RG states
        self.update_rg_states(ranked_responses, selected_response_rg)

        # Update the entity tracker with the response
        self.state_manager.current_state.entity_tracker.update_from_rg(selected_response, selected_response_rg, self.state_manager.current_state)

        # If the response needs a prompt, get prompts
        if selected_response.needs_prompt:

            # If we need a prompt, set the selected response RG in the state so that prompting RGs can condition on it
            setattr(self.state_manager.current_state, 'selected_response_rg', selected_response_rg)

            # Get prompts from RGs, ranked by priority
            exclude_rgs = [selected_response_rg] if selected_response_rg != 'FALLBACK' else []  # don't run responding RG, unless it's FALLBACK
            logger.primary_info(f'Getting prompts from RGs...')
            ranked_prompts = self.run_rgs_and_rank('prompt', exclude_rgs)

            # Check that the top prompt isn't offensive (and remove it if it is)
            ranked_prompts = self.remove_offensive(ranked_prompts)

            # Choose the top prompt
            selected_prompt, selected_prompt_rg = ranked_prompts.top_result, ranked_prompts.top_rg
            logger.debug('Selected prompt from {}: {}'.format(selected_prompt_rg, selected_prompt),
                                extra={'color_msg_by_component': selected_prompt_rg})

            # Update the RG states
            self.update_rg_states(ranked_prompts, selected_prompt_rg)

            # Update the entity tracker with the prompt
            self.state_manager.current_state.entity_tracker.update_from_rg(selected_prompt, selected_prompt_rg, self.state_manager.current_state)

        else:
            selected_prompt, selected_prompt_rg = None, None

        return selected_response_rg, selected_response, selected_prompt_rg, selected_prompt


    def init_rg_states(self):
        """
        Initializes self.state_manager.current_state.response_generator_states, a dict from rg_name (str) to RG state.
        If it's the first turn of the conversation, run RGs' init_state fns.
        Otherwise get RG states from state_manager.last_state.
        """

        # If it's not the first turn, get RG states from last_state
        if self.state_manager.last_state:
            rg_states = copy.copy(self.state_manager.last_state.response_generator_states)
            logger.primary_info('Loaded these RG states from last_state:\n{}'.format(
                print_dict_linebyline(rg_states)), extra={'color_lines_by_component': True})

            # Check for any RGs that don't have a state. Could be because their state became stale due to timeouts
            rgs_without_state = [rg_name for rg_name in self.response_generators.name_to_class if
                                 rg_name not in rg_states]

            # If so, run init_state for those RGs. This seems like the best possible graceful degradation.
            if len(rgs_without_state) > 0:
                logger.warning('These RG states do not exist in last_state:\n{}'.format(rgs_without_state))
                new_rg_states = self.response_generators.run_multithreaded(
                    rg_names=rgs_without_state,
                    function_name='init_state',
                    timeout=DialogManager.INIT_STATE_TIMEOUT)
                logger.primary_info('Ran init_state fns for RGs with missing states; got these states:\n{}'.format(
                    print_dict_linebyline(new_rg_states)), extra={'color_lines_by_component': True})
                for rg in new_rg_states:
                    rg_states[rg] = new_rg_states[rg]

        # If it's the first turn, run RGs' init_state() fns
        else:
            rg_states = self.response_generators.run_multithreaded(rg_names=self.response_generators.name_to_class.keys(),
                                          function_name='init_state',
                                          timeout=DialogManager.INIT_STATE_TIMEOUT)
            logger.primary_info("Ran RGs' init_state functions and got these states:\n{}".format(
                print_dict_linebyline(rg_states)), extra={'color_lines_by_component': True})

        # Put in current_state
        setattr(self.state_manager.current_state, 'response_generator_states', rg_states)
        logger.info(f"Current rg states are {rg_states}")


    def update_rg_states(self, results: RankedResults, selected_rg: str):
        """
        Run update_state_if_chosen fn for selected_rg, and update_state_if_not_chosen for all other RGs.
        Then update self.state_manager.current_state.response_generator_states with the new RG states.

        Inputs:
            results: RankedResults. contains the results from all RGs.
            selected_rg: str, one of the RGs in results. The chosen RG
        """
        rg_states = self.state_manager.current_state.response_generator_states

        # Get the args needed for the update_state_if_chosen fn. That's (state, conditional_state) for selected_rg
        args_list = [[rg_states[selected_rg], results[selected_rg].conditional_state]]

        # Run update_state_if_chosen for selected_rg
        logger.info(f'Starting to run update_state_if_chosen for {selected_rg}...')
        output = self.response_generators.run_multithreaded(rg_names=[selected_rg],
                                                            function_name='update_state_if_chosen',
                                                    args_list=args_list, timeout=DialogManager.UPDATE_STATE_TIMEOUT)

        if selected_rg not in output:
            logger.error('Tried to run {}\'s update_state_if_chosen function with conditional_state={} but there was '
                         'an error or timeout, so no update was made'.format(selected_rg, results[selected_rg].conditional_state))
        else:
            rg_states[selected_rg] = output[selected_rg]
            logger.primary_info('Ran {}\'s update_state_if_chosen function with:\nconditional_state={}.\nGot new state={}'.format(
                selected_rg, results[selected_rg].conditional_state, output[selected_rg]), extra={'color_msg_by_component': selected_rg})

        # Get the args needed for the update_state_if_not_chosen fn. That's (state, conditional_state) for all RGs except selected_rg
        other_rgs = [rg for rg in results.keys() if rg != selected_rg and not is_killed(results[rg])]
        logger.info(f"now, current states are {rg_states}")

        def rg_was_taken_over(rg):
            if self.state_manager.last_state:
                logger.debug(f"Rg that is selected is {selected_rg}. Currently evaluated rg is {rg}. "
                             f"rg == self.state_manager.last_state.active_rg is {rg == self.state_manager.last_state.active_rg}")
                return rg_states[selected_rg].rg_that_was_taken_over and rg == self.state_manager.last_state.active_rg
            else:
                return None

        args_list = [[rg_states[rg], results[rg].conditional_state, rg_was_taken_over(rg)] for rg in other_rgs]

        # Run update_state_if_not_chosen for other RGs
        logger.info(f'Starting to run update_state_if_not_chosen for {other_rgs}...')
        output = self.response_generators.run_multithreaded(rg_names=other_rgs, function_name='update_state_if_not_chosen',
                                                    args_list=args_list, timeout=DialogManager.UPDATE_STATE_TIMEOUT)

        # Save the updated states in rg_states
        for rg in other_rgs:
            if rg not in output:
                logger.error('Tried to run {}\'s update_state_if_not_chosen function with conditional_state={} but there was an '
                             'error or timeout, so no update was made'.format(rg, results[rg].conditional_state))
            else:
                rg_states[rg] = output[rg]
                logger.info('Ran {}\'s update_state_if_not_chosen function with:\nconditional_state={}\nGot new state={}'.format(
                    rg, results[rg].conditional_state, output[rg]), extra={'color_msg_by_component': rg})


    def run_rgs_and_rank(self, phase: str, exclude_rgs : List[str] = []) -> RankedResults:
        """
        Run RGs' get_response/get_prompt (depending on phase).
        Save RG states that are returned in the ResponseGeneratorResults/PromptResults.
        Sort the results by priority.

        Arguments:
            phase: 'response' or 'prompt'; the phase you want to run
            exclude_rgs: list of RGs that you DON'T want to run

        Returns:
            ranked_results: RankedResults, ordered by descending priority.
        """
        assert phase in ['response', 'prompt'], "phase={} not one of 'response' or 'prompt'".format(phase)
        rg_states = self.state_manager.current_state.response_generator_states

        # Get list of RGs to run (all except exclude_rgs, and any that don't have a state due to an earlier error)
        rgs_list = []
        for rg in self.response_generators.name_to_class:
            if rg in exclude_rgs or self.state_manager.current_state.turn_num == 0 and rg not in ('LAUNCH', 'FALLBACK'):
                continue
            if rg in rg_states:
                rgs_list.append(rg)
            else:
                logger.warning('{} has no state in self.state_manager.current_state.response_generator_states, '
                               'so not running it for {} phase'.format(rg, phase))

        # Get the states for the RGs we'll run, which we'll use as input to the get_response/get_prompt fn
        logger.debug('Copying RG states to use as input...')

        # import pdb; pdb.set_trace()

        # Get results from the RGs in parallel, running either get_response or get_prompt.
        # results_dict is a dict mapping from RG name to a ResponseGeneratorResult/PromptResult
        timeout = DialogManager.GET_RESPONSE_TIMEOUT if phase == 'response' else DialogManager.GET_PROMPT_TIMEOUT
        last_state_active_rg = self.state_manager.last_state_active_rg
        if last_state_active_rg and self.state_manager.last_state_response.answer_type in CONTINUING_ANSWER_TYPES:
            priority_modules = [last_state_active_rg]
        else:
            priority_modules = []

        rg_was_taken_over = None
        if self.state_manager.last_state_response:
            rg_was_taken_over = self.state_manager.last_state_response.state.rg_that_was_taken_over

        def rg_to_resume(rg):
            logger.debug(f"rg that was taken over is {rg_was_taken_over}. Currently evaluated rg is {rg}. "
                         f"rg == rg_was_taken_over is {rg == rg_was_taken_over}.")
            return rg == rg_was_taken_over

        function_name = 'get_prompt_wrapper' if phase == 'prompt' else 'get_response'
        args_list = copy.copy([[rg_states[rg], rg_to_resume(rg)] for rg in rgs_list])
        results_dict = self.response_generators.run_multithreaded(rg_names=rgs_list,
                                         function_name=function_name,
                                         timeout=timeout,
                                         args_list=args_list,        # [[state] for state in input_rg_states],
                                         priority_modules=priority_modules)

        # Log the initial results
        logger.primary_info('RG {} results:\n{}'.format(phase, print_dict_linebyline(results_dict)), extra={'color_lines_by_component': True})

        # Check results are correct type
        correct_result_type = ResponseGeneratorResult if phase == 'response' else PromptResult
        for rg in list(results_dict.keys()):
            result = results_dict[rg]
            if not isinstance(result, correct_result_type):
                logger.error('{} returned a {} of type {} instead of {}. Removing it from results.'.format(
                    rg, phase, type(result), correct_result_type))
                del results_dict[rg]

        # Put results_dict in current_state
        setattr(self.state_manager.current_state, f'{phase}_results', results_dict)

        # Update rg_states with the new RG states given in the ResponseGeneratorResults/PromptResults.
        # Since the response_generator_runner can time out, not all RGs would return results.
        # in which case their internal state would be inconsistent and cannot be used subsequently
        # for example, its internal tracking of the state machine would now be incorrect.
        # It is safest to remove this RG from all subsequent turns
        # Keeping only valid states in rg_states achieves this purpose
        for rg in list(rg_states.keys()):
            if rg in rgs_list:  # If the rg's phase function was run
                if rg in results_dict:
                    if is_killed(results_dict[rg]):
                        logger.primary_info(f'{rg} was killed during get_{phase}, so its state will be retained.')
                    else:
                        rg_states[rg] = results_dict[rg].state

                else:  # If it gave an error or timed out, delete the state as it will be inconsistent
                    logger.warning(f'{rg} had an error or timed out during get_{phase}, so its state is no longer correct. '
                                   'Deleting its state from self.state_manager.current_state.response_generator_states')
                    del rg_states[rg]

        # Sort results using priority ranking strategy
        if phase == 'response':
            ranked_results = self.ranking_strategy.rank_responses(results_dict)
        else:
            turns_since_last_active = None
            if hasattr(self.state_manager.current_state, 'turns_since_last_active'):
                turns_since_last_active = self.state_manager.current_state.turns_since_last_active
            ranked_results = self.ranking_strategy.rank_prompts(results_dict, turns_since_last_active) # type: ignore

        # Log the results, sorted by priority
        logger.primary_info('RG {} results (highest priority first):\n{}'.format(phase, print_dict_linebyline(ranked_results)), extra={'color_lines_by_component': True})

        return ranked_results

    @measure
    def remove_offensive(self, ranked_results: RankedResults) -> RankedResults:
        """
        Check the top-ranked response/prompt in ranked_results for offensiveness. If it's inoffensive, do nothing.
        If it's offensive, remove it from ranked_results, and start again by checking the second-ranked response/prompt.

        Arguments:
            ranked_results: RankedResults (responses or prompts from RGs).

        Returns:
            ranked_results, potentially with some results removed, so that the top result is guaranteed to be
            inoffensive.
        """
        top_result = ranked_results.top_result
        top_rg = ranked_results.top_rg
        logger.info(f'Checking top-priority {type(top_result).__name__} from {top_rg} for offensiveness: "{top_result.text}"')
        if contains_offensive(top_result.text):
            logger.error(f'{top_rg} gave an offensive result (i.e. the contains_offensive function returned True). '
                         f'This should be caught inside the RG! Offensive text: "{top_result.text}"')
            ranked_results.remove_result(top_rg)
            return self.remove_offensive(ranked_results)  # start again, checking the new top result
        else:
            return ranked_results
