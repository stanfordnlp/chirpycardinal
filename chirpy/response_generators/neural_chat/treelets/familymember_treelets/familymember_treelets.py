import logging
import random
from typing import Optional, Tuple, List
from chirpy.response_generators.neural_chat.treelets.abstract_treelet import Treelet
from chirpy.response_generators.neural_chat.state import State, ConditionalState
from chirpy.response_generators.neural_chat.treelets.familymember_treelets.util import UserFamilyMember, OLDER_FAMILY_MEMBERS, FRIENDS, PARTNERS, SIBLINGS_AND_COUSINS, KIDS, PETS
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, ResponsePriority, PromptType


logger = logging.getLogger('chirpylogger')

PROMPT_TRANSITIONS = [
    "Oh hey,",
    "Hmm, so,",
    "By the way,",
    "Oh, I just remembered,",
]


class FamilyMemberTreelet(Treelet):
    _launch_appropriate = False
    _use_neg_answer_as_negnav = True  # if the user says "no" after starter question, interpret as negnav and end conversation
    _user_family_members = []  # the specific UserFamilyMembers covered by this treelet
    return_question_answers = []

    @property
    def user_family_members(self) -> List[UserFamilyMember]:
        if not self._user_family_members:
            raise NotImplementedError()
        else:
            return self._user_family_members

    def get_family_member_by_trigger_phrase(self, trigger_phrase: str) -> UserFamilyMember:
        """Returns the UserFamilyMember with trigger_phrase"""
        for user_family_member in self.user_family_members:
            if trigger_phrase in user_family_member.trigger_phrases:
                return user_family_member
        raise ValueError(f"There is no user_family_member in {self.name} with trigger_phrase '{trigger_phrase}'")

    def update_state(self, state: State):
        """
        This function is run for each treelet on every turn (before getting response).
        It can be used to update the state based on "listening in" to the conversation, even if the treelet isn't
        going to produce a response on this turn.
        """
        # For all user_family_members, check if their trigger phrases were mentioned on this turn, and if so, add to trigger_phrases_mentioned in state
        for user_family_member in self.user_family_members:
            trigger_phrase, posnav = user_family_member.get_mentioned_trigger_phrase(self.state_manager.current_state)
            if trigger_phrase:
                turn_num = self.state_manager.current_state.turn_num
                logger.primary_info(f'{self.name} detected the user mentioning "{trigger_phrase}" on this turn ({turn_num}) with posnav={posnav}')
                state.add_mentioned_trigger_phrase(self.name, trigger_phrase, turn_num, posnav)


    def get_starter_question_and_labels_for_family_member(self, state: State, user_family_member, current_turn: bool):
        """
        Returns a tuple of:
            - A starter question (str), or None (if it's not appropriate for this treelet to ask a starter question at this time).
            - Labels for the starter question, that should go in the state.
        """

        # Sample a strategy that hasn't been used before (for any family member, in any treelet)
        strategy2starterq = user_family_member.strategy2starterq
        available_strategies = [s for s in strategy2starterq if s not in state.used_bot_labels]
        if not available_strategies:
            logger.primary_info(f'{self.name} has no available strategies left for {user_family_member}')
            return None, []
        strategy = random.choice(available_strategies)
        logger.primary_info(f'{self.name} uniformly sampled the strategy "{strategy}" for {user_family_member} from {available_strategies}')

        # Choose least repetitive starter question for this strategy
        starter_q = self.choose(strategy2starterq[strategy])

        # Choose least repetitive "you mentioned" phrase for this strategy
        you_mentioned = self.choose(user_family_member.you_mentioned if current_turn else user_family_member.you_mentioned_earlier)

        # Choose least repetitive bridge phrase for this strategy
        bridge = self.choose(user_family_member.bridges(starter_q))

        # Make the utterance
        utterance = "{} {} {}".format(you_mentioned, bridge, starter_q)

        # Return
        return utterance, [strategy]


    def get_starter_question_and_labels(self, state: State, for_response: bool = False, for_launch: bool = False) -> Tuple[Optional[str], List[str]]:
        """
        Inputs:
            for_response: if True, the provided starter question will be used to make a response. Otherwise, used to make a prompt.

        Returns a tuple of:
            - A starter question (str), or None (if it's not appropriate for this treelet to ask a starter question at this time).
            - Labels for the starter question, that should go in the state.
            - priority: ResponsePriority or PromptType
        """

        # Get the most recent trigger phrase for this treelet
        if self.name not in state.conv_histories:  # if this treelet has no ConvHistory, do nothing
            trigger_phrase, turn_num, posnav = None, None, None
        else:
            trigger_phrase, turn_num, posnav = state.conv_histories[self.name].most_recent_trigger

        # If there has been a trigger phrase for this treelet, potentially give the starter question
        if trigger_phrase:
            trigger_on_current_turn = turn_num==self.state_manager.current_state.turn_num  # bool
            logger.primary_info(f'In {self.name}, the most recent trigger phrase is "{trigger_phrase}" on turn {turn_num} (trigger_on_current_turn={trigger_on_current_turn}) with posnav={posnav}.')

            # If we're writing a response and the most recent trigger phrase didn't happen on this turn, do nothing
            if for_response and not trigger_on_current_turn:
                logger.primary_info(f'In {self.name}, the most recent trigger phrase is "{trigger_phrase}" on turn {turn_num} with posnav={posnav}, which is not this turn, so giving no response.')
                return None, [], None

            # Get the starter question for the user_family_member mentioned by the trigger_phrase
            user_family_member = self.get_family_member_by_trigger_phrase(trigger_phrase)
            starter_question, bot_labels = self.get_starter_question_and_labels_for_family_member(state, user_family_member, current_turn=trigger_on_current_turn)

            # For response, determine priority (FORCE_START only if trigger phrase mentioned with posnav on this turn)
            if for_response:
                priority = ResponsePriority.FORCE_START if posnav and trigger_on_current_turn else ResponsePriority.CAN_START

            # For prompt, determine priority (CURRENT_TOPIC only if trigger phrase mentioned with posnav on this turn)
            # Also add a prompt transition phrase
            else:
                priority = PromptType.CURRENT_TOPIC if posnav and trigger_on_current_turn else PromptType.CONTEXTUAL
                prompt_transition_phrase = self.choose(PROMPT_TRANSITIONS)
                starter_question = "{} {}".format(prompt_transition_phrase, starter_question)

            return starter_question, bot_labels, priority

        # If the user hasn't mentioned any trigger phrases, return nothing
        return None, [], None

    @property
    def return_question_answer(self) -> str:
        """Gives a response to the user if they ask the "return question" to our starter question
        
        DEPRECATED -- No need w/ blenderbot"""
        if not self.return_question_answers:
            raise NotImplementedError()
        return self.choose(self.return_question_answers)

    def edit_history_for_remote(self, history: List[str]) -> List[str]:
        """
        Returns the history as it should be given as input to remote module

        Inputs:
            history: odd-length list of strings, starting and ending with user utterances, as it exists in the
                neuralchat state.

        Returns:
            new_history: odd-length list of strings, starting and ending with user utterances, as it should be fed to remote module
        """
        # Override the abstract class's function which only uses the "question part" of the starter question
        # We want to include the whole starter question (including "you mentioned your sister") because it gives necessary context
        return history




class OlderFamilyMembersTreelet(FamilyMemberTreelet):
    fallback_response = "It's so nice to hear about your family."
    return_question_answers = [
        "I don't have a family myself, but I think human relationships are wonderful.",
        "Personally, I don't have a family, but I think family is very important.",
    ]
    _user_family_members = OLDER_FAMILY_MEMBERS

class FriendsTreelet(FamilyMemberTreelet):
    fallback_response = "It's so nice to hear about your friends."
    return_question_answers = [
        "Speaking for myself, I make lots of friends through conversations",
    ]
    _user_family_members = FRIENDS

class PartnersTreelet(FamilyMemberTreelet):
    fallback_response = "It's so nice to hear about your partner."
    return_question_answers = [
        "I don't have a partner myself, but I'm a big romantic at heart!",
    ]
    _user_family_members = PARTNERS

class SiblingsCousinsTreelet(FamilyMemberTreelet):
    fallback_response = "It's so nice to hear about your family."
    return_question_answers = [
        "I don't have a family myself, but I think human relationships are wonderful.",
        "Personally, I don't have a family, but I think family is very important.",
    ]
    _user_family_members = SIBLINGS_AND_COUSINS

class KidsTreelet(FamilyMemberTreelet):
    fallback_response = "It's so nice to hear about your children."
    return_question_answers = [
        "I don't have any kids myself, but I think being a parent is one of the most important jobs in the world.",
    ]
    _user_family_members = KIDS

class PetsTreelet(FamilyMemberTreelet):
    fallback_response = "It's so nice to hear about your furry family members."
    return_question_answers = [
        "It's hard for me to keep a pet in the cloud, but if I could, I think a sloth would be nice to keep me company.",
    ]
    _user_family_members = PETS
