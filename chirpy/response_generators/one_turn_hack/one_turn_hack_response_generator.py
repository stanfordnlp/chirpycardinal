import logging
from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import emptyResult, ResponseGeneratorResult, PromptResult, emptyPrompt, \
    UpdateEntity
from chirpy.core.regex.templates import MyNameIsNonContextualTemplate, MyNameIsNotTemplate
from chirpy.core.util import contains_phrase
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name
from chirpy.core.smooth_handoffs import SmoothHandoff
from chirpy.response_generators.one_turn_hack.responses import *
from chirpy.response_generators.one_turn_hack.one_turn_hack_utils import *
from chirpy.response_generators.one_turn_hack.regex_templates import *
from chirpy.response_generators.one_turn_hack.state import State, ConditionalState

logger = logging.getLogger('chirpylogger')


class OneTurnHackResponseGenerator(ResponseGenerator):
    name='ONE_TURN_HACK'
    def __init__(self, state_manager):
        super().__init__(state_manager, state_constructor=State,
                         conditional_state_constructor=ConditionalState)

    def talk_about_george_floyd(self) -> bool:
        if self.state.talked_about_blm:
            return False
        return contains_phrase(self.utterance, ['floyd', 'floyds', "floyd's", "ahmaud", "arbery", "arberys", "breonna"]) and \
                contains_phrase(self.utterance, ['know', 'talk', 'tell', 'think', 'you'])

    def handle_default_post_checks(self):
        state, utterance, response_types = self.get_state_utterance_response_types()
        nav_intent_output = self.get_navigational_intent_output()
        if self.talk_about_george_floyd():
            blm_entity = get_entity_by_wiki_name("Black Lives Matter")
            return ResponseGeneratorResult(text=RESPONSE_TO_QUESTION_ONE_GEORGE_FLOYD,
                                           priority=ResponsePriority.FORCE_START,
                                           needs_prompt=True, state=self.state,
                                           cur_entity=blm_entity,
                                           conditional_state=ConditionalState(talked_about_blm=True),
                                           smooth_handoff=SmoothHandoff.ONE_TURN_TO_WIKI_GF)

        # Check for chatty phrases in utterance
        chatty_slots = ChattyTemplate().execute(utterance)
        my_name_slots = MyNameIsNonContextualTemplate().execute(utterance)
        not_my_name_slots = MyNameIsNotTemplate().execute(utterance)
        say_that_again_slots = SayThatAgainTemplate().execute(utterance)
        request_name_slots = RequestNameTemplate().execute(utterance)
        request_story_slots = RequestStoryTemplate().execute(utterance)
        compliment_slots = ComplimentTemplate().execute(utterance)
        request_age_slots = RequestAgeTemplate().execute(utterance)

        # logger.primary_info(f"Request name is present: {request_name_slots is not None}")
        if chatty_slots is not None:
            pass
            # chatty_phrase = chatty_slots["chatty_phrase"]
            # logger.primary_info('Detected chatty phrase intent with slots={}'.format(chatty_slots))

            # # Step 3: Get response from dictionary of hand-written responses
            # response, needs_prompt = one_turn_responses[chatty_phrase]
            # logger.primary_info('Chatty RG returned user_response={}'.format(response))

            # Check for user correcting their name
        elif (my_name_slots and self.get_last_active_rg() and self.get_last_active_rg() != 'LAUNCH') or not_my_name_slots: # TODO: fold into utility
            logger.primary_info('User is attempting to correct name.')
            response = "Oops, it sounds like I got your name wrong. I'm so sorry about that! I won't make that mistake again."
            needs_prompt = True
            setattr(self.state_manager.user_attributes, 'name', None)
            setattr(self.state_manager.user_attributes, 'discussed_aliens', False)

        # # Check for user asking to repeat
        elif say_that_again_slots is not None: # TODO: fold into the abrupt_initiative_check
            logger.primary_info('One-turn-hack detected say-that-again intent - changing topic')
            CLARIFICATION_COMPLAINT_RESPONSE = [
                "Oh no, I think I wasn't clear. Let's talk about something else.",
                "It sounds like I wasn't clear. Can we move onto something else?"
            ]
            response, needs_prompt = self.choose(CLARIFICATION_COMPLAINT_RESPONSE), True

        elif request_name_slots is not None: #  TODO: fold into utility
            logger.primary_info('One-turn-hack detected user requesting name')
            user_name = getattr(self.state_manager.user_attributes, 'name', None)
            if user_name:
                response, needs_prompt = f"If I remember correctly, your name is {user_name}.", True
            else:
                response, needs_prompt = "From what I recall, you didn't give me your name.", True

        elif request_story_slots is not None: # TODO: fold into utility
            logger.primary_info("One-turn-hack detected user requesting a story")
            response, needs_prompt = "Sure, here's a personal story someone once shared with me. " + random.choice(STORIES), False

        elif is_game_or_music_request(self, utterance):
            pass
            # response, needs_prompt = f"It sounds like you want me to play something. " \
            #                         f"I'm actually an Alexa socialbot, so I cannot play any songs or games, sorry about that! " \
            #                         f"If you want to stop chatting, you can end our conversation by saying, stop. Otherwise, " \
            #                         f"we could talk about something else!", False

        elif compliment_slots is not None and "not" not in utterance: # TODO: fold into utility
            logger.primary_info("User has praised Alexa")
            response, needs_prompt = "Thank you, I'm so glad you feel that way! It's nice to know you're enjoying this conversation.", True

        elif request_age_slots is not None: # TODO: fold into utility
            response, needs_prompt = "It's hard to say since I don't have a real birthday!", True
        # Check for user hesitating while trying to navigate to a topic
        elif nav_intent_output.pos_intent and nav_intent_output.pos_topic_is_hesitate and "depends on" not in utterance: # TODO: fold into utiltiy
            logger.primary_info('User has PositiveNavigationalIntent with topic=HESITATE, so asking them for topic again')
            response, needs_prompt = "I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?", False

        # Check for user giving general positive talking intent (e.g. "i want to chat")
        # If WIKI is supposed to handle the utterance and it contains tell, it typically means user is asking for more info (and hence doesn't really specify topic)
        elif nav_intent_output.pos_intent and nav_intent_output.pos_topic is None and not \
            (self.state_manager.last_state_active_rg in ['WIKI', 'NEWS'] and contains_phrase(utterance, {'tell'})): # TODO: fold into utility  (holding pattern)
            logger.primary_info('User has PositiveNavigationalIntent with topic=None, so ONE_TURN_HACK is responding with "What would you like to talk about?"')
            response, needs_prompt = "Ok, I'd love to talk to you! What would you like to talk about?", False

        # Otherwise return empty
        else:
            return self.emptyResult()

        # Step 7: set priority
        priority = ResponsePriority.NO
        is_safe = True
        logger.primary_info(f"OTH got {response}")
        # Step 8: return result
        return ResponseGeneratorResult(text=response, priority=priority,
                                       needs_prompt=needs_prompt, state=self.state,
                                       cur_entity=None, conditional_state=self.state)
