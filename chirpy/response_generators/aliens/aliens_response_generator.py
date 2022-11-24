"""
RG for the bot's pet topic after at least 15 turns in the conversation have taken place.
"""
from chirpy.core.response_generator import *
from chirpy.core.response_generator_datatypes import AnswerType
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.response_generators.aliens.treelets import *
from chirpy.response_generators.aliens.aliens_helpers import *
from chirpy.response_generators.aliens.state import State, ConditionalState
from chirpy.response_generators.aliens.aliens_helpers import ResponseType

logger = logging.getLogger('chirpylogger')

SPACE_ENTITIES = ["Outer space", "Haumea", "Extraterrestrial life", "Alien (law)", "Planet"]

class AliensResponseGenerator(ResponseGenerator):
    name = "ALIENS"
    def __init__(self, state_manager) -> None:

        # self.introductory_treelet = IntroductoryTreelet(self)
        # self.first_turn_treelet = FirstTurnTreelet(self)
        # self.second_turn_treelet = SecondTurnTreelet(self)
        # self.third_turn_treelet = ThirdTurnTreelet(self)
        # self.fourth_turn_treelet = FourthTurnTreelet(self)
        # self.fifth_turn_treelet = FifthTurnTreelet(self)
        # self.question_treelet = QuestionTreelet(self)
        self.god_treelet = SymbolicTreelet(self, 'aliens')

        treelets = {
            treelet.name: treelet for treelet in [self.god_treelet]
        }

        super().__init__(state_manager, treelets=treelets, can_give_prompts=True, state_constructor=State,
                         conditional_state_constructor=ConditionalState) # ,transition_matrix=self.init_transition_matrix()


    def identify_response_types(self, utterance):
        response_types = super().identify_response_types(utterance)

        if is_opinion(self, utterance):
            response_types.add(ResponseType.OPINION)

        return response_types

    # def init_transition_matrix(self):
    #     return {
    #         self.introductory_treelet.name: {
    #             ResponseType.NO: self.handle_rejection_response,
    #             ResponseType.YES: (self.first_turn_treelet, ResponsePriority.STRONG_CONTINUE),
    #             lambda state, response_types: True: (self.first_turn_treelet, ResponsePriority.WEAK_CONTINUE)
    #         },
    #         self.question_treelet.name: {
    #             lambda state, response_types: True: self.handle_rejection_response
    #         }
    #     }

    # def handle_question(self):
    #     return self.question_treelet.get_question_response()

    # def handle_rejection_response(self, prefix='', main_text=None, suffix='',
    #                               priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
    #                               conditional_state=None, answer_type=AnswerType.ENDING):
    #     # logger.primary_info(f"ALIENS state, utt, response_types {self.get_state_utterance_response_types()}")
    #     good_listener = "You're such a great listener!"
    #     prefix, priority = {
    #         self.introductory_treelet.name: ("Sure, no worries.", ResponsePriority.STRONG_CONTINUE),
    #         self.first_turn_treelet.name: (f"Sure, thanks for letting me share my thoughts on this. {good_listener}",
    #                                        ResponsePriority.STRONG_CONTINUE),
    #         self.second_turn_treelet.name: (f"Sure, thanks for letting me talk so much about this! {good_listener}",
    #                                         ResponsePriority.STRONG_CONTINUE),
    #         self.third_turn_treelet.name: (f"Sure, thanks for letting me ramble on for so long about this! {good_listener}",
    #                                        ResponsePriority.STRONG_CONTINUE),
    #         self.fourth_turn_treelet.name: (f"Sure, thanks for letting me ramble on for so long about this! {good_listener}",
    #                                         ResponsePriority.STRONG_CONTINUE),
    #         self.question_treelet.name: ("Anyway, ", ResponsePriority.STRONG_CONTINUE),
    #         self.fifth_turn_treelet.name: ("", ResponsePriority.WEAK_CONTINUE)
    #     }[self.state.cur_supernode]
    #     return super().handle_rejection_response(prefix=prefix, suffix=suffix, priority=priority,
    #                                              needs_prompt=needs_prompt,
    #                                              conditional_state=conditional_state)

    def handle_custom_continuation_checks(self):
        """
        If the user says NO to some of our ALIENS questions (e.g. Isn't that intriguing? Isn't that mysterious?),
        we take it that the user is disinterested and exit.
        :return:
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        # if self.state.prev_treelet_str in [self.third_turn_treelet.name, self.fourth_turn_treelet.name]:
        if self.state.cur_supernode in ['aliens_fourth_turn', 'aliens_fifth_turn']:
            if ResponseType.NO in response_types and len(utterance.split()) <= 5:
                main_text = "Well, that's unfortunate. I've always thought there was something magical and mysterious " \
                            "about the stars. But let's talk about something you're more interested in! What would " \
                            "you like to talk about next?"
                conditional_state = ConditionalState(prev_treelet_str='', next_treelet_str=None)
                return super().handle_rejection_response(main_text=main_text, needs_prompt=False,
                                                         conditional_state=conditional_state,
                                                         answer_type=AnswerType.QUESTION_HANDOFF)


    def handle_current_entity(self):
        current_entity = self.get_current_entity(initiated_this_turn=True)
        priority = self._get_priority_from_answer_type()
        if current_entity is not None and current_entity.name in SPACE_ENTITIES:
            # response = self.first_turn_treelet.get_response(priority)
            self.state.entering_aliens = True
            response = self.god_treelet.get_response(priority)
            response.text = "Sure! " + response.text
            return response

    def handle_user_attributes(self):
        if self.state.cur_supernode == 'aliens_second_turn':
            self.set_user_attribute("discussed_aliens", True)

    # def get_prompt(self, state): only used for debugging
    #     prompt = super().get_prompt(state)
    #     logger.primary_info(f"Aliens RG returned prompt: {prompt}")
    #     return prompt
