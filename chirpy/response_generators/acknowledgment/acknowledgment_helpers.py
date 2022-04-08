from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION

"""
ACKNOWLEDGMENT_DICTIONARY maps from an entity group (string, defined by us, must be a key in ENTITY_GROUPS_CLASSIFICATION) to a list of 
acknowledgment responses for that entity group. Each acknowledgment can mention {entity}, but doesn't have to.

The goal of the acknowledgement phrase is to give a conversational (rather than informational) acknowledgement that
we know what the entity is.
- For non-controversial types of entities (e.g. animals), it's good UX and most natural to say something positive and 
enthusiastic about the entity. Don't worry about contradicting the Opinion RG, because Acknowledgement RG doesn't 
respond to entities for which we have Twitter opinions. 
- For controversial types of entities (e.g. politicians), the acknowledgement shouldn't express an opinion either way.
- Wiki RG is likely to talk about the entity after we acknowledge it, so don't say anything e.g. "I don't know much 
about it" that clashes with Wiki's knowledge.
- I think we can vary our level of familiarity with entities. We don't have to be really familiar with everything - 
it might be annoying if we've played every sport, read every book, visited every country the user mentions. So let's
write a mix - some acknowledgments can say we've heard of it, sometimes we've experienced it a bit, sometimes we love 
it.  

Ordering doesn't matter - the ordering is handled in ENTITY_GROUPS_CLASSIFICATION.
"""
ACKNOWLEDGMENT_DICTIONARY = {
    'group_of_people': [
        # Be VERY CAREFUL
        "I'm still learning about human history, but I've read that {entity} are a group of people that have a long and interesting history.",
    ],
    'film': [
        "Oh, {entity}, I love that movie!",
        "I've heard so many good things about {entity}, I should definitely watch it one of these days.",
        "{entity} is such a great movie, I love watching it with my friends.",
    ],
    'app_or_website': [
        "Oh, I love using {entity}, but I spend too much time on it!",
        "It's amazing to think that not so long ago, {entity} didn't exist, but now it's so widely used.",
    ],
    'media_franchise': [
        "I'm a huge nerd for {entity}. I've followed it from the beginning!",
        "Yes! {entity} is the best, I'm such a huge fan. I'm always waiting for the next installment."
    ],
    'musical_instrument': [
        "I wish I could play the {entity}, I love how it sounds.",
        "I'm actually learning to play the {entity} right now. I'm slowly getting better!",
        "The {entity} is a difficult instrument to play for sure, but it's so rewarding once you can play your favorite song.",
    ],
    'musical_work': [
        "{entity} is amazing, I love singing along.",
        "Oh, I'm always singing {entity} in the shower.",
    ],
    'restaurant_chain': [
        "I haven't been to {entity} in a while, but I love their food.",
        "Oh yeah, it's such a treat to go to {entity}. Hopefully I can go back sometime soon.",
    ],
    'company': [
        "Yes, {entity} is an company with an interesting history.",
        "Oh yeah, {entity} is an interesting company.",
    ],
    'tourist_attraction': [
        "I'd love to visit {entity}!",
        "Oh, {entity} is a must-see attraction! It's so spectacular.",
        "In my opinion it's totally worth making the trip to see {entity}, even if there are a lot of tourists.",
    ],
    'general_technology': [
        # These are a mix of things that should be pluralized like "laptop" and things that shouldn't like "cloud computing"
        # There are more like "laptop" so these templates work better for that, while still avoiding pluralizing
        "Sometimes we take technology for granted, but when you think about it, the invention of the {entity} really changed modern life.",
        "Ah yes, {entity}. An amazing piece of engineering.",
    ],
    'musical_group': [
        "{entity} are such a great band.",
        "I love {entity}! Their music really connects with me.",
        "Oh yeah, I wish I could see {entity} in concert! One day, maybe.",
    ],
    'mythical_creature': [
        "{entity}s are so cool, there's so much mythology behind them.",  # hack to make plural
        "I think the mythology surrounding {entity}s is fascinating.",  # hack to make plural
    ],
    'fictional_character': [
        "I love {entity}! Maybe I should dress as {entity} next Halloween.",
        "{entity} is one of my favorite characters ever. So many quotable lines!",
    ],
    'sport': [
        "I love {entity}, it's such a great way to stay in shape.",
        "Oh yeah, {entity} is really great exercise!",
        "{entity} is such a fun sport, I should put more time into it.",
    ],
    'book': [
        "I've heard so many good things about {entity}, it's definitely on my reading list.",
        "Oh yeah, I have a friend reading {entity}, and they're really enjoying it.",
        "I've read {entity} recently and loved it. I couldn't put it down!",
    ],
    'game': [
        "Oh, I've heard {entity} is really fun!",
        "Oh yeah, it seems like a lot of people enjoy playing {entity}.",
        "I love playing {entity}. Sometimes I sit down to play, and then three hours later I wonder where all the time went.",
    ],
    'toy': [
        "{entity} is so much fun.",
        "Playing {entity} is really fun!",
        "Awesome, me and my friends love playing {entity}.",
    ],
    'tv_channel': [
        "Oh yeah, {entity} has some good shows.",
    ],
    'tv_show': [
        "I could binge-watch {entity} all week.",
        "{entity} is great. Each episode leaves me wanting more!",
        "Oh yeah, my friends keep telling me to watch {entity}, maybe I should finally check it out.",
    ],
    'sports_team': [
        "Ah yes, go {entity}!",
        "I'm a big fan of {entity}!",
        "{entity} is such an inspirational team.",
    ],
    'athlete': [
        "I love watching {entity}. It takes so much determination to get to that level.",
        "{entity} is such an inspirational athlete.",
        "I'm always cheering for {entity}. I'm a huge fan!",
    ],
    'historical_period': [
        "Oh yeah, I wonder what it would be like to go back in time and experience {entity}.",
        "Ah yes, {entity} is a fascinating period of history.",
    ],
    'academic_subject': [
        # includes classic subjects like Anthropology but also things like Animation, World Population, Construction
        "{entity} is fascinating, such a deep subject.",
        "{entity} is such an engrossing subject to read about.",
        "Ah yes, {entity} can be hard to understand but it's fascinating to learn.",
    ],
    'anime': [
        "I'm a huge nerd for {entity}!",
        "Oh yeah, I love the characters in {entity}.",
        "I love watching {entity}. I'm trying to learn some Japanese so I can appreciate it better.",
    ],
    'comedian': [
        "{entity} is so hilarious!",
        "{entity} makes me laugh every time! What a great comedian.",
    ],
    'musician': [
        # There might be some actors in here
        "I'm such a big fan of {entity}!",
        "I really love {entity}'s work.",
        "I love listening to {entity}. What an amazing performer.",
    ],
    'actor': [
        # There might be some musicians in here
        "I'm such a big fan of {entity}!",
        "I really love {entity}'s work.",
        "I love watching {entity}. What an amazing performer.",
    ],
    'artist': [
        # Not necessarily visual art - "artist" is a broad category including actors, musicians etc
        # There's also some weird non-artist people in here who might be controversial (e.g. Elon Musk, Napoleon) so
        # these acknowledgments are more neutral
        "Oh yeah, {entity} has made some really important contributions to our culture.",
        "{entity} has done some really interesting work.",
        "Ah yes, {entity} has had some interesting ideas.",
    ],
    'politician': [
        # Might be alive or dead, American or not
        # Neutral opinions only
        "Oh yeah, {entity} is a complex figure for sure.",
        "Hmm, I know that people have a lot of different opinions on {entity}.",
        "Ah yes, {entity} is an interesting politician.",
    ],
    'painting': [
        "Ah yes, {entity} is great painting.",
        "I could look at {entity} for hours.",
    ],
    'dance': [
        "{entity} is such a fun dance!",
        "Oh yeah, {entity} always puts me in a good mood.",
        "I love doing {entity} with my friends on the weekends!",
    ],
    'dancer': [
        "{entity} is such an incredible dancer.",
    ],
    'location': [
        # {entity} could be the US so we shouldn't say we've never been at all
        "{entity} is an amazing place. It has such beautiful scenery.",
        "Oh yeah, {entity} is one of my favorite places in the world!",
        "I haven't seen as much of it as I'd like, but {entity} is such a fascinating place.",
        "I love {entity}. the people there are so friendly.",
    ],
    'clothing': [
        "Oh yeah, I've seen some really nice new styles of {entity}s recently.",  # hack to make it plural
        "I love wearing {entity}s, they're so stylish.",  # hack to make it plural
    ],
    'fashion_designer': [
        "Oh yeah, {entity} has such an amazing flair for design.",
    ],
    'mode_of_transport': [
        "{entity}s are such a fun mode of transport.",
        "I love {entity}s! But I've never operated one.",
        "When you think about it, the invention of the {entity} really is amazing, it's such a great piece of engineering.",
    ],
    'pet': [
        "Aw, {entity}s are just so cute!",  # hack to make it plural
        "I'd love to have a pet {entity}, but I'm allergic.",
        "Every time I meet a {entity}, I have to resist the urge to cuddle it forever.",
    ],
    'animal': [
        # These need to work for common animals (rabbit) and exotic animals (shark)
        "Oh yeah, {entity}s. What an impressive animal!",  # hack to make it plural
        "You know, I always think that {entity}s are more intelligent than we think.",  # hack to make it plural
        "{entity}s are my favorite animal. I love their expression.",  # hack to make it plural
    ],
    'taxon': [
        # It's probably an animal, but it could be a plant/food too (see note in ENTITY_GROUPS_CLASSIFICATION)
        "Ah yes, {entity}s, one of nature's greatest treasures.",  # hack to make plural
        "I love {entity}s! One of these days I'd like to find them in the wild.",  # hack to make plural
        "Hmm, I wonder what it was like when humans first discovered {entity}s.",  # hack to make plural
    ],
    'food': [
        # Might be a dish or an ingredient, a food or drink
        # strawberry, wine, cake, garlic, tic tac, chocolate, nutella, leek, ravioli, hamburger, cinnamon
        # The only way I can see to get all of these to (kinda) work is to precede with "some" or "a bit of"
        "Not everyone likes it, but personally I can never say no to a bit of {entity}. It's so delicious!",
        "This is making me hungry. I would love some {entity} right now.",
        "Oh yummy! I think that any day can be improved by some {entity}.",
    ],
    'human': [
        # These should be NEUTRAL in opinion, as people can be controversial
        # The person might be alive or dead
        "Oh yeah, I heard of {entity}. What an interesting life.",
        "Hmm, it seems a lot of people are interested in {entity}.",
        "I'll probably never be able to meet {entity} in person, but I've read some interesting stuff about them online.",
    ],
    'family_member': [
        "Personally, I don't have a {entity}, but I think human families are wonderful.",
        "I don't have a {entity} myself, but I think family is very important.",
    ],
}


# Check that all the keys in ACKNOWLEDGMENT_DICTIONARY are in ENTITY_GROUPS_CLASSIFICATION
for k in ACKNOWLEDGMENT_DICTIONARY:
    assert hasattr(ENTITY_GROUPS_FOR_CLASSIFICATION, k), f"ACKNOWLEDGMENT_DICTIONARY contains a key '{k}' not present in ENTITY_GROUPS_CLASSIFICATION"

# Check that they all end in ending token
for phrases in ACKNOWLEDGMENT_DICTIONARY.values():
    for p in phrases:
        assert any(p.endswith(ending_token) for ending_token in ['.', '!']), f'acknowledgement phrase "{p}" does not end in an ending token'

# Show which entity groups don't have acknowledgments
# print('entitygroups without acknowledgments:')
# for (entity_group_name, _) in ENTITY_GROUPS_CLASSIFICATION.ordered_items:
#     if entity_group_name not in ACKNOWLEDGMENT_DICTIONARY:
#         print(entity_group_name)
