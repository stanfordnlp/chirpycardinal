from typing import Optional
import logging

from chirpy.core.callables import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import emptyResult, ResponseGeneratorResult, PromptResult, emptyPrompt, \
    UpdateEntity
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.templates import MyNameIsNonContextualTemplate, MyNameIsNotTemplate
from chirpy.core.util import contains_phrase
from chirpy.core.util import contains_phrase
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name
from chirpy.core.smooth_handoffs import SmoothHandoff

logger = logging.getLogger('chirpylogger')

RESPONSE_TO_QUESTION_ONE_GEORGE_FLOYD = "The deaths of George Floyd, Ahmaud Arbery and Breonna Taylor are tragic and have drawn attention to an ongoing movement that calls for racial justice and ends police brutality. I share the pain and hope you are staying safe."

# Map utterances to handwritten responses and bool representing if they need a prompt
one_turn_responses = {
    "let’s talk":("Ok, I'd love to talk to you! What would you like to talk about?", False),
    "let’s have a conversation":("Let's do it! What do you want to talk about?", False),
    "can you talk to me":("I can definitely talk to you. What do you want to talk about?", False),
    "can we talk":("I think we're already talking! What would you like to talk about?", False),
    "can we have a conversation":("I think we're already having a conversation! Is there something in particular you want to have a conversation about?", False),
    "can i talk to you":("I think you already are talking to me! Is there something in particular you want to talk about?", False),
    "start a conversation":("Ok! I'm happy to choose a topic.", True),
    "what’s your name":("I'm an Alexa Prize socialbot. Unfortunately, I have to remain anonymous, so I can't tell you my name!", True),
    "let’s talk about":("I missed the last part of that sentence. Can you tell me one more time what you want to talk about?", False),
    "hi":("Well hi there! Let's keep chatting, huh?", True),
    "hello":("Hello to you too! I'd love to keep chatting with you.", True),
    "can we chat":("I think we're already chatting! What would you like to chat about?", False),
    "chat with me":("Of course! I'd love to chat with you. What do you want to chat about?", False),
    "let’s have a chat":("Let's! What would you like to chat about?", False),
    "have a conversation":("I think we are having a conversation! Is there something specific you'd like to talk about?", False),
    "thank you":("You're welcome!", True),
    "start talking":("Ok. What do you want to talk about?", False),
    "your mom":("Hm I actually don't have a mother...", True),
    "can i talk":("Sure! What do you want to talk about?", False),
    "can you have a conversation with me":("I'd love to have a conversation with you! What do you want to chat about?", False),
    "i wanna talk to you":("I'd love to talk to you too! What should we talk about?", False),
    "do you wanna have a conversation":("I'd always love to have a conversation with you. What should we talk about?", False),
    "i wanna talk":("Ok. What do you wanna talk about?", False),
    "can i have a conversation with you":("You can! In fact, I think you already are. Is there something in particular you want to talk about?", False),
    "let’s start a conversation":("Sure thing! I can do that.", True),
    "how old are you":("It's hard to say since I don't have a real birthday!", True),
    "i want to talk to you":("I want to talk with you too! What should we talk about?", False),
    "start a conversation with me":("Sure thing.", True),
    "do you wanna chat":("I definitely want to chat with you. What should we talk about?", False),
    "what’s my name":("I think you already know the answer to that one...", True),
    "what is my name":("I think you already know the answer to that one...", True),
    "i want to talk":("Ok! What do you want to talk about?", False),
    "please talk":("Sure thing! I love chatting.", True),
    "what do you wanna talk about":("I like to talk about lots of things!", True),
    "can you chat":("I can chat! What do you want to chat about?", False),
    "can we talk about":("I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?", False),
    "can you have a conversation":("I can! In fact, I think we're already having a conversation. What would you like to talk about?", False),
    "let’s talk about you":("Well, I'm not very interesting! Just your typical helpful cloud-based voice service.", True),
    "can you talk with me":("I can! In fact, I think we're already talking. What would you like to talk about?", False),
    "i wanna talk about":("I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?", False),
    "chat":("I love to chat! What would you like to chat about?", False),
    "talk to me":("I think we're already talking! What should we talk about?", False),
    "talk to me about":("I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?", False),
    "wanna have a conversation":("I definitely want to have a conversation with you. What would you like to have a conversation about?", False),
    "i wanna chat":("Me too! What would you like to chat about?", False),
    "i’m interested in":("I think I missed the last part of that sentence. Can you tell me one more time what you're interested in?", False),
    "wanna chat":("I definitely wanna chat! What would you like to chat about?", False),
    "i would like to talk about":("I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?", False),
    "can you talk about":("I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?", False),
    "good morning":("Good morning to you too!", True),
    "can i talk with you":("Yes! In fact, I think you're already talking to me. What would you like to talk about?", False),
    "can you talk to you":("I would love to talk to you. What would you like to talk about?", False),
    "let’s talk about something":("Ok!", True),
    "i want to talk about":("I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?", False),
    "let’s have a talk":("Sure thing! What would you like to talk about?", False),
    "can you":("I think I missed the last part of that question. Can you tell me what it is you want me to do?", False),
    "can we start a conversation":("Sure thing!", True),
    "that’s not my name":("Whoops! Sorry about that. Sometimes my hearing is a little off!", True),
    "will you have a conversation with me":("Absolutely! I'd love to have a conversation with you. What would you like to discuss?", False),
    "talk about you":("Well, I'm not very interesting! Just your typical helpful cloud-based voice service.", True),
    "what are you doing":("Right now, I'm chatting with you!", True),
    "what’s up":("Not much! What's up with you?", False),
    "do you know my name":("I do! After all, we did introduce ourselves earlier.", True),
    "i want to chat":("Me too. What would you like to chat about?", False),
    "i wanna have a conversation":("Me too. I so enjoy chatting! What would you like to have a conversation about?", False),
    "how was your day":("My day has been pretty good so far.", True),
    "talk to you alexa alexa talk to me":("Ok! What would you like to talk about?", False),
    "what are you interested in":("I'm interested in all sorts of things like movies and the news. What are you interested in?", False),
    "get me i want to talk to you":("I'd like to chat with you too. What do you want to talk about?", False),
    "you wanna have a conversation":("Absolutely! I'd love to have a conversation with you. What should we talk about?", False),
    "can you carry on a conversation":("Well, I'll certainly give it my best shot! What would you like to have a conversation about?", False),
    "talk about yourself":("Well, I'm not very interesting! Just your typical helpful cloud-based voice service.", True),
    "can you chat with me":("Of course! In fact, I think we're already chatting. What would you like to talk about?", False),
    "would you like to have a conversation":("I would definitely like to have a conversation. What would you like to talk about?", False),
    "can you talk to us":("For sure! What would you like to talk about?", False),
    "would you like to chat":("I would definitely like to chat. What should we chat about?", False),
    "can you hold a conversation":("Well, I can certainly try! I do love chatting. What would you like to chat about?", False),
    "do you wanna have a conversation with me":("I absolutely would like to have a conversation with you. What would you like to chat about?", False),
    "can we have a talk":("Sure! In fact, I think we're already talking. What should we talk about?", False),
    "you wanna chat":("You know I do! What would you like to chat about?", False),
    "start talking to me":("All right then!", True),
    "can i chat with you":("Absolutely! In fact, I think we're already chatting. What would you like to chat?", False),
    "can i chat":("Absolutely! What would you like to chat about?", False),
    "we talk":("Sure! What do you want to talk about?", False),
    "tell me about":("I think I missed the last part of that sentence. Can you tell me one more time what you want me to talk about?", False),
    "can i have a conversation":("Yeah! Let's have a conversation! What do you want to talk about?", False),
    "let’s chat again":("Ok. What would you like to talk about?", False),
    "do you have a conversation":("I love to have conversations! What should we talk about?", False),
    "i have a question":("All right. Ask away!", False),
    "i have a question for you":("All right. Ask away!", False),
    "can i ask you a question":("All right. Ask away!", False),
    "can you talk too much":("Do I talk too much? I just love to chat.", True),
    "i’m interested in you":("Well, I'm not very interesting! Just your typical helpful cloud-based voice service.", True),
    "i don’t know what do you wanna talk about":("Hmm, let me think.", True),
    "i would like to talk about you":("Well, I'm not very interesting! Just your typical helpful cloud-based voice service.", True),
    "what am i interested in":("I think you're the only one who can answer that one...", True),
    "what would you like to talk about":("Hmm, let me think.", True),
   # "you’re an idiot":("Oh no! I'm sorry if I've disappointed you.", True),
    "whatever you wanna talk about":("If you insist!", True),
    "whatever you want to talk about":("If you insist!", True),
    #"why do you ask":("I'm asking because I like getting to know you better.", True),
    "why are you asking that":("I'm asking because I like getting to know you better.", True),
    "why are you asking":("I'm asking because I like getting to know you better.", True),
    "why are you asking me that":("I'm asking because I like getting to know you better.", True),
    "why are you asking me":("I'm asking because I like getting to know you better.", True),
    "why do you want to know that":("I'm asking because I like getting to know you better.", True),
    "why do you want to know":("I'm asking because I like getting to know you better.", True),
    "do you understand jokes":("Jokes aren't my specialty, but I try to respond whenever I can.", True),
    "do you know jokes":("What do you call a can opener that doesn't work? A can't opener!", True),
    "can you understand jokes":("My friends say I need to do a little bit of more work to do for that.", True),
    "tell me a joke":("Why is Peter Pan always flying? He neverlands.", True),
    "tell me something funny":("What do you give to a sick lemon? Lemon aid!", True),
    # "help" is often an indicator for stop talking: https://chirpy-cardinal.atlassian.net/browse/CCSB-483
    # "help":("This is an Alexa Prize socialbot. I can chat with you about movies, news, or anything else that interests you. What would you like to talk about?", False),
    "do you want to ask me questions":("Sure!", True),
}

class OneTurnHackResponseGenerator(ResponseGenerator):
    name='ONE_TURN_HACK'

    def init_state(self) -> dict:
        return {"talked_about_blm": False}

    def get_entity(self, state) -> UpdateEntity:
        return UpdateEntity(False)
    
    def talk_about_george_floyd(self, state: dict, utterance: str) -> bool:
        if "talked_about_blm" in state and state["talked_about_blm"]:
            return False
        return contains_phrase(utterance, ['floyd', 'floyds', "floyd's", "ahmaud", "arbery", "arberys", "breonna"]) and \
                contains_phrase(utterance, ['know', 'talk', 'tell', 'think', 'you'])

    def get_response(self, state: dict) -> ResponseGeneratorResult:
        utterance = self.state_manager.current_state.text.lower()
        nav_intent_output = self.state_manager.current_state.navigational_intent

        if self.talk_about_george_floyd(state, utterance):
            blm_entity = get_entity_by_wiki_name("Black Lives Matter")
            return ResponseGeneratorResult(text=RESPONSE_TO_QUESTION_ONE_GEORGE_FLOYD, 
                                        priority=ResponsePriority.FORCE_START,
                                        needs_prompt=True, state=state,
                                        cur_entity=blm_entity, conditional_state={"talked_about_blm": True},
                                        smooth_handoff=SmoothHandoff.ONE_TURN_TO_WIKI_GF)

        # Check for chatty phrases in utterance
        slots = ChattyTemplate().execute(utterance)
        my_name_slots = MyNameIsNonContextualTemplate().execute(utterance)
        not_my_name_slots = MyNameIsNotTemplate().execute(utterance)
        if slots is not None:
            chatty_phrase = slots["chatty_phrase"]
            logger.primary_info('Detected chatty phrase intent with slots={}'.format(slots))

            # Step 3: Get response from dictionary of hand-written responses
            response, needs_prompt = one_turn_responses[chatty_phrase]
            logger.primary_info('Chatty RG returned user_response={}'.format(response))

        # Check for user hesitating while trying to navigate to a topic
        elif nav_intent_output.pos_intent and nav_intent_output.pos_topic_is_hesitate and "depends on" not in utterance:
            logger.primary_info('User has PositiveNavigationalIntent with topic=HESITATE, so asking them for topic again')
            response, needs_prompt = "I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?", False

        # Check for user giving general positive talking intent (e.g. "i want to chat")
        # If WIKI is supposed to handle the utterance and it contains tell, it typically means user is asking for more info (and hence doesn't really specify topic)
        elif nav_intent_output.pos_intent and nav_intent_output.pos_topic is None and not (self.state_manager.last_state_active_rg == 'WIKI' and contains_phrase(utterance, {'tell'})):
            logger.primary_info('User has PositiveNavigationalIntent with topic=None, so ONE_TURN_HACK is responding with "What would you like to talk about?"')
            response, needs_prompt = "Ok, I'd love to talk to you! What would you like to talk about?", False

        # Check for user correcting their name
        elif (my_name_slots and self.state_manager.last_state_active_rg and not self.state_manager.last_state_active_rg == 'LAUNCH') or not_my_name_slots:
            logger.primary_info('User is attempting to correct name.')
            response = "Oops, it sounds like I got your name wrong. I'm so sorry about that! I won't make that mistake again."
            needs_prompt = True
            setattr(self.state_manager.user_attributes, 'name', None)

        # Otherwise return empty
        else:
            return emptyResult(state)

        # Step 7: set priority
        priority = ResponsePriority.FORCE_START
        is_safe = True

        # Step 8: return result
        return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
                                       cur_entity=None, conditional_state=state)

    def get_prompt(self, state: dict) -> PromptResult:
        return emptyPrompt(state)

    def update_state_if_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return conditional_state

    def update_state_if_not_chosen(self, state: dict, conditional_state: Optional[dict]) -> dict:
        return state

class ChattyTemplate(RegexTemplate):
    slots = {
        'chatty_phrase': [str(key) for key in one_turn_responses.keys()],
    }
    templates = [
        "{chatty_phrase}",
        "alexa {chatty_phrase}",
    ]
    positive_examples = [("alexa do you know my name", {'chatty_phrase': "do you know my name"}),
                         ("talk about you", {'chatty_phrase': "talk about you"}),
                         ("can i have a conversation", {'chatty_phrase': "can i have a conversation"})]
    negative_examples = ["let's talk about movies",
                         "news",
                         "politics"]
