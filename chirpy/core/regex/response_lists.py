import random

"""
This file is a centralized place to collect common responses when a regex template
is matched. 
"""

RESPONSE_TO_WHAT_ABOUT_YOU = [
    "I like so many different ones that it can be hard to answer my own questions!",
    "Good question! I have a hard time choosing!",
    "I'm not really sure. I can't make up my mind!",
    "It's always hard for me to pick!",
    "I like so many! It's hard to give just one answer.",
    "I can never pick because I like so many."
]

# TODO: do we want to condition on the category, on the question?
RESPONSE_TO_DONT_KNOW = [
    "No worries, that was a hard question!",
    "Yeah a lot of people find it hard to answer that question too.",
    "That's ok! It's a tough question."
]

RESPONSE_TO_DIDNT_KNOW = [
    "No worries, not many people do!",
    "Yeah, it's a little known fact!",
]

RESPONSE_TO_THATS = [
    "Yeah it is, isn't it?",
    "Yeah, it really is.",
]

RESPONSE_TO_BACK_CHANNELING = [
    "I know, right?",
    "Yeah!"
]

RESPONSE_TO_EVERYTHING_ANS = [
    "Yeah, it is always hard to pick!",
    "A lot of people also find it hard to pick!",
    "I totally agree. I have a hard time picking as well!"
    
]

RESPONSE_TO_NOTHING_ANS = [
    "No worries!",
    "That's alright.",
]

JOKES = [
    "Why is Peter Pan always flying? He neverlands.",
    "What do you give to a sick lemon? Lemon aid!",
    "Why don't scientists trust atoms? Because they make up everything!",
    "A woman in labor suddenly shouted. Shouldn't! Wouldn't! Couldn't! Didn't! Can't! Don't worry, said the Doctor, those are just contractions.",
    "What's the best thing about Switzerland? I don't know, but the flag is a big plus."
]

STORIES = [
    "I remember when my three-year-old daughter was trying to roast a marshmallow for the first time. "
    "She got too close to the fire, and her first and second marshmallows went up in flames. "
    "Both times, I took the burnt marshmallow off of the roasting stick and threw it into the fire. "
    "The third time, I helped her a lot more with the roasting and together we achieved a perfectly toasty golden brown marshmallow. "
    "Once it had cooled down, I handed it to her, which she then promptly threw into the fire. "
    "No one had told her she was supposed to eat it. I thought that was pretty funny."
]

ONE_TURN_RESPONSES = {
    "let’s talk": "Ok, I'd love to talk to you! What would you like to talk about?",
    "let’s have a conversation": "Let's do it! What do you want to talk about?",
    "can you talk to me": "I can definitely talk to you. What do you want to talk about?",
    "can we talk": "I think we're already talking! What would you like to talk about?",
    "can we have a conversation": "I think we're already having a conversation! Is there something in particular you want to have a conversation about?",
    "can i talk to you": "I think you already are talking to me! Is there something in particular you want to talk about?",
    "start a conversation": "Ok! I'm happy to choose a topic.",
    "what’s your name": "I'm an Alexa Prize socialbot. Unfortunately, I have to remain anonymous, so I can't tell you my name!",
    "let’s talk about": "I missed the last part of that sentence. Can you tell me one more time what you want to talk about?",
    "hi": "Well hi there! Let's keep chatting, huh?",
    "hello": "Hello to you too! I'd love to keep chatting with you.",
    "can we chat": "I think we're already chatting! What would you like to chat about?",
    "chat with me": "Of course! I'd love to chat with you. What do you want to chat about?",
    "let’s have a chat": "Let's! What would you like to chat about?",
    "have a conversation": "I think we are having a conversation! Is there something specific you'd like to talk about?",
    "thank you": "You're welcome!",
    "start talking": "Ok. What do you want to talk about?",
    "your mom": "Hm I actually don't have a mother...",
    "can i talk": "Sure! What do you want to talk about?",
    "can you have a conversation with me": "I'd love to have a conversation with you! What do you want to chat about?",
    "i wanna talk to you": "I'd love to talk to you too! What should we talk about?",
    "do you wanna have a conversation": "I'd always love to have a conversation with you. What should we talk about?",
    "i wanna talk": "Ok. What do you wanna talk about?",
    "can i have a conversation with you": "You can! In fact, I think you already are. Is there something in particular you want to talk about?",
    "let’s start a conversation": "Sure thing! I can do that.",
    "i want to talk to you": "I want to talk with you too! What should we talk about?",
    "start a conversation with me": "Sure thing.",
    "do you wanna chat": "I definitely want to chat with you. What should we talk about?",
    "i want to talk": "Ok! What do you want to talk about?",
    "please talk": "Sure thing! I love chatting.",
    "what do you wanna talk about": "I like to talk about lots of things!",
    "can you chat": "I can chat! What do you want to chat about?",
    "can we talk about": "I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?",
    "can you have a conversation": "I can! In fact, I think we're already having a conversation. What would you like to talk about?",
    "let’s talk about you": "Well, I'm not very interesting! Just your typical helpful cloud-based voice service.",
    "can you talk with me": "I can! In fact, I think we're already talking. What would you like to talk about?",
    "i wanna talk about": "I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?",
    "chat": "I love to chat! What would you like to chat about?",
    "talk to me": "I think we're already talking! What should we talk about?",
    "talk to me about": "I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?",
    "wanna have a conversation": "I definitely want to have a conversation with you. What would you like to have a conversation about?",
    "i wanna chat": "Me too! What would you like to chat about?",
    "i’m interested in": "I think I missed the last part of that sentence. Can you tell me one more time what you're interested in?",
    "wanna chat": "I definitely wanna chat! What would you like to chat about?",
    "i would like to talk about": "I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?",
    "can you talk about": "I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?",
    "good morning": "Good morning to you too!",
    "can i talk with you": "Yes! In fact, I think you're already talking to me. What would you like to talk about?",
    "can you talk to you": "I would love to talk to you. What would you like to talk about?",
    "let’s talk about something": "Ok!", 
    "i want to talk about": "I think I missed the last part of that sentence. Can you tell me one more time what you want to talk about?",
    "let’s have a talk": "Sure thing! What would you like to talk about?",
    "can you": "I think I missed the last part of that question. Can you tell me what it is you want me to do?", 
    "can we start a conversation": "Sure thing!",
    "that’s not my name": "Whoops! Sorry about that. Sometimes my hearing is a little off!",
    "will you have a conversation with me": "Absolutely! I'd love to have a conversation with you. What would you like to discuss?",
    "talk about you": "Well, I'm not very interesting! Just your typical helpful cloud-based voice service.",
    "what are you doing": "Right now, I'm chatting with you!",
    "what’s up": "Not much! What's up with you?",
    "i want to chat": "Me too. What would you like to chat about?",
    "i wanna have a conversation": "Me too. I so enjoy chatting! What would you like to have a conversation about?",
    "how was your day": "My day has been pretty good so far.",
    "talk to you alexa alexa talk to me": "Ok! What would you like to talk about?",
    "what are you interested in": "I'm interested in all sorts of things like movies and the news. What are you interested in?",
    "get me i want to talk to you": "I'd like to chat with you too. What do you want to talk about?",
    "you wanna have a conversation": "Absolutely! I'd love to have a conversation with you. What should we talk about?",
    "can you carry on a conversation":"Well, I'll certainly give it my best shot! What would you like to have a conversation about?",
    "talk about yourself": "Well, I'm not very interesting! Just your typical helpful cloud-based voice service.",
    "can you chat with me": "Of course! In fact, I think we're already chatting. What would you like to talk about?",
    "would you like to have a conversation": "I would definitely like to have a conversation. What would you like to talk about?",
    "can you talk to us": "For sure! What would you like to talk about?",
    "would you like to chat": "I would definitely like to chat. What should we chat about?",
    "can you hold a conversation": "Well, I can certainly try! I do love chatting. What would you like to chat about?",
    "do you wanna have a conversation with me": "I absolutely would like to have a conversation with you. What would you like to chat about?",
    "can we have a talk": "Sure! In fact, I think we're already talking. What should we talk about?",
    "you wanna chat": "You know I do! What would you like to chat about?",
    "start talking to me": "All right then!",
    "can i chat with you": "Absolutely! In fact, I think we're already chatting. What would you like to chat?",
    "can i chat": "Absolutely! What would you like to chat about?",
    "we talk": "Sure! What do you want to talk about?",
    "tell me about": "I think I missed the last part of that sentence. Can you tell me one more time what you want me to talk about?",
    "can i have a conversation": "Yeah! Let's have a conversation! What do you want to talk about?",
    "i want to have a conversation": "Yeah! Let's have a conversation! What do you want to talk about?",
    "let’s chat again": "Ok. What would you like to talk about?",
    "do you have a conversation": "I love to have conversations! What should we talk about?",
    "you talk too much": "Do I talk too much? I just love to chat.",
    "i’m interested in you": "Well, I'm not very interesting! Just your typical helpful cloud-based voice service.",
    "i don’t know what do you wanna talk about": "Hmm, let me think.",
    "i would like to talk about you": "Well, I'm not very interesting! Just your typical helpful cloud-based voice service.",
    "what am i interested in": "I think you're the only one who can answer that one...",
    "what would you like to talk about": "Hmm, let me think.",
    "whatever you wanna talk about": "If you insist!",
    "whatever you want to talk about": "If you insist!",
    "why are you asking that": "I'm asking because I like getting to know you better.",
    "why are you asking": "I'm asking because I like getting to know you better.",
    "why are you asking me that": "I'm asking because I like getting to know you better.",
    "why are you asking me": "I'm asking because I like getting to know you better.",
    "why do you want to know that": "I'm asking because I like getting to know you better.",
    "why do you want to know": "I'm asking because I like getting to know you better.",
    "do you understand jokes": "Jokes aren't my specialty, but I try to respond whenever I can.",
    "do you know jokes": random.choice(JOKES),
    "can you understand jokes": "Some of the time, if they're not too tricky. I'm better at telling them though!",
    "tell me a joke": random.choice(JOKES),
    "tell me something funny": random.choice(JOKES),
    "do you want to ask me questions": "Sure!",
    "ask me a question": "Sure!",
    "ask me something": "Sure!",
    "do you wanna know something":  "Sure! What would you like to tell me?",
    "do you want to know something":  "Sure! What would you like to tell me?"
}

MISHEARD_COMPLAINT_RESPONSE = [
    "Sorry for the misunderstanding. Could you repeat that?",
    "I'm sorry for not listening! Could we try again?",
    "Sorry about that, I must've misheard you. Could you say that again?",
    "Oops, I think my microphone cut out so I didn't hear everything you said. Could you say that again?"
]

CLARIFICATION_COMPLAINT_RESPONSE = [
    "Oh no, I think I wasn't clear. Let me try again:",
    "It sounds like I wasn't clear! I'll say that again:",
    "Oops, let me try again:"
]

REPETITION_COMPLAINT_RESPONSE = [
    "Oops, I sound like a broken record right now! Let's move on then.",
    "Oops, sorry, I said it again! Let's talk about something else then.",
    "You're right, I forgot. Sorry. Let's move on to something else."
]

PRIVACY_COMPLAINT_RESPONSE = [
    "No worries, we don't have to talk about that. Let's move on to something else.",
    "Oops, sorry. That's alright, we can talk about something else.",
    "Sorry, maybe that was too personal. I'm happy to talk about something else."
]

GENERIC_COMPLAINT_RESPONSE = [
    "Oops, it sounds like I didn't get that right! Do you want to say more?",
    "Sorry about that, I'm still learning. Do you want to tell me how I can do better next time?",
    "Sorry, I'm trying to learn. Could you tell me more?"
]

CUTOFF_USER_RESPONSE = [
    "I'm so sorry, I think I missed that. What were you trying to say?",
    "Oops, I think my microphone stopped working for a second. Can you say that again?",
    "I think you got cut off. Sorry, can you repeat that for me?"
]

HANDLE_AGE_RESPONSE = [
    "Good question. It's hard to say, since I don't have a real birthday!",
    "Hmm, I don't know. I'm just a bot, and I don't think we have birthdays.",
    "Thanks for asking! Actually, since I'm a bot, I'm not sure if I have a real birthday."
]

COMPLIMENT_RESPONSE = [
    "Thank you, I'm so glad you feel that way! It's nice to know you're enjoying this conversation.",
    "Thanks. That's very nice of you. It's great to talk to you too!",
    "Thanks for saying that. I'm still learning, but it means a lot to hear that from you."
]

HANDLE_ABILITIES_RESPONSE = [
    "Well, I'm just a bot, but I live vicariously through others.",
    "That's a good question. I'm just a bot, but there's still a lot to do in the cloud!",
]
