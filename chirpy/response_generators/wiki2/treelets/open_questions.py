from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION

"""
OPEN_QUESTION_DICTIONARY maps from an entity group (string, defined by us, must be a key in ENTITY_GROUPS_FOR_CLASSIFICATION) to a dicionary of
open questions for that entity group. Each question can mention {entity}, but doesn't have to. The dictionary maps from
what we expect the user to talk about. In some cases these are also entity groups. This type information isn't currently
used to link the entities in the response. It is only used to keep track of what sort of questions have been asked. Some
of expected type annotations are quite arbitrary and is only used as a tool to group simliar questions together.

The goal of the open question is to ask a question that would lead to an infromational conversation. The answers to
questions should lead to some sort of a match in wikipedia articles
- For controversial types of entities (e.g. politicians), the question shouldn't express an opinion either way.

Ordering doesn't matter - the ordering is handled in ENTITY_GROUPS_FOR_CLASSIFICATION.

Some of these questions try to get to entities, but we want entity tracker to not set them directly, rather we want
WIKI to give a connecting response before changing the entity. So we're not setting the entity type here, but rather doing
contextual entity switch based on overlap of linked entities with wikipedia article
"""
OPEN_QUESTIONS_DICTIONARY = {

    'film': {
        'fictional_character': ["What do you think about the characters in {entity}, who would you say is your favorite?"],
        'plot': ["What did you like about plot of {entity}?"],
        'actor': ["I think the actors in {entity} are pretty good too. Who did you like?"],
    },

    #['Guitar', 'Piano', 'Drum kit', 'Violin', 'Trumpet', 'Ukulele', 'Viola', 'Vocaloid', 'Flute', 'Electric guitar',
    #'Bass guitar', 'Cello', 'Clarinet']
    'musical_instrument': {
        'misc': ["What do you like about listening to the {entity}?"],
        'musician': ['Who would be your favorite {entity} player?'],
    },

    # 'Yummy (Justin Bieber song)', 'Hamilton (musical)', 'Hero (2019 Tamil film)', 'Graduation (album)', 'Hallelujah (Leonard Cohen song)',
    # 'Baby Shark', 'Calm (album)', 'Horses (album)', 'Lover (album)', 'Hurt (Nine Inch Nails song)', 'Dirt (Alice in Chains album)',
    # 'The End (The Doors song)', 'Cool (Jonas Brothers song)', 'Lemonade (Beyoncé album)',
    # This seems to include both songs and albums
    'musical_work': {
        'lyrics': ["What did you think about the lyrics of {entity}?"],
    },

    #["McDonald's", 'Taco Bell', 'Starbucks', "Wendy's", 'Subway (restaurant)', 'The Cheesecake Factory', 'Burger King',
    # "Domino's Pizza", 'KFC', 'Popeyes', "Dunkin' Donuts", 'Dairy Queen', 'Pizza Hut']
    'restaurant_chain': {
        'food': ["What do you think about their menu, any favorites?"],
    },

    'tourist_attraction': {
        'poi': ["I'm thinking about visiting {entity} but I'm not sure what to do when I'm there. Do you have any thoughts about what I should do?",
                "When I visit places, I love to take some unique photos. Do you have any ideas for where I could take a cool selfie in {entity}?" ]
    },
    # ['Ghost (Swedish band)', 'Scooter (band)', 'Imagine Dragons', 'BTS (band)', 'The Beatles', 'America (band)',
    # 'Eagles (band)', 'Fun (band)', 'Pink Floyd', 'The Cure', 'The Rolling Stones', 'Metallica', 'Led Zeppelin',
    # 'Heart (band)', 'Cream (band)']
    'musical_group': {
        'concert': ["Have you been to any concerts by {entity}?"],
        'musician': ["Who do you think is the soul of {entity}?"]
    },

    #['Unicorn', 'Dragon', 'Mermaid', 'Fairy', 'Angel', 'Zombie', 'Vampire', 'Griffin', 'Bigfoot', 'Werewolf', 'Athena',
    # 'Cupid', 'Oni', 'Loch Ness Monster', 'Phoenix (mythology)', 'Manticore']
    'mythical_creature': {
        'story': ["{entity}s have so many fantastical abilities. If you were one, what would you like to do?"],
    },

    #'Mario', 'Batman', 'Superman', 'Elsa (Frozen)', 'Yoda', 'Percy Jackson', 'Superhero', 'Mickey Mouse', 'Kirby (character)',
    #'Thing (comics)', 'Hermione Granger', 'Spider-Man', 'Goofy',
    'fictional_character': {
        'story': ["{entity} has done so many amazing things! What are some of your favorite {entity} moments?",
                  "{entity} has got into so many adventures! What are some adventures that you've enjoyed?",
                  "If you were {entity} for a day, what would you want to do?"]
        #'story': ["{entity} does so many interesting things! What was the most memorable one for you?"],
    },
    # ['Golf', 'Basketball', 'Baseball', 'Football', 'Yoga', 'Volleyball', 'Gymnastics', 'Softball',
    'sport': {
        'tournament' : ["Many sports seem to have tournaments these days. Is there any {entity} tournament that you follow?"]
    },
    # unfortunately doesn't work for Bible, Quran, Gospel, so they are blacklisted in wiki
    #['Harry Potter', 'Bible', 'My Hero Academia', 'The Hunger Games', 'Quran', 'Gospel', 'Attack on Titan', 'Gospel of Matthew',
    #'The Jungle', '1Q84', 'Black Butler', 'Guinness World Records', 'Kama Sutra', 'The Crucible', "Charlotte's Web", 'On the Road',
    # 'Noragami', 'Warriors (novel series)', 'Doctor Dolittle',
    'book': {
        'fictional_character': ["Who did you like the most in {entity}?"],
        'plot': ["What did you think of {entity}'s story?"],
    },

    #['Animal Crossing', 'Minecraft', 'Fortnite', 'Roblox', 'Monopoly (game)', 'Apex Legends', 'Overwatch (video game)',
    # 'Grand Theft Auto', 'Terraria', 'Fortnite Battle Royale', 'Halo (franchise)', 'Bendy and the Ink Machine', 'Fallout (series)',
    'game': {
        'misc': ["What do you like about {entity}'s gameplay?"],
    },

    #['YouTube (channel)', 'Netflix', 'CNN', 'Pain', 'Disney Channel', 'Cartoon Network', 'ESPN', 'PBS',
    #'Nickelodeon', 'Smosh', 'Umami', 'RT (TV network)', 'Lifetime (TV network)', 'Fox News', 'Fox Broadcasting Company',
    #'Autonomous sensory meridian response']
    'tv_channel': {
        'tv_show': ["What do you watch on {entity}?"],
    },

    # ['Friends', 'Fridays (TV series)', 'South Park', 'Outlander (TV series)', 'Stranger Things', 'The Office (American TV series)', 'The Flash (2014 TV series)',
    # 'Mom (TV series)', 'The Simpsons', 'Riverdale (2017 TV series)', 'Victorious', 'Wings (1990 TV series)', 'Gravity Falls', 'House (TV series)',
    'tv_show': {
        'fictional_character': ["What do you think about the characters in {entity}, who would you say is your favorite?"],
        'actor': ["I think the actors in {entity} are pretty good too. Who did you like?"],
        'plot': ["What did you like about {entity}'s plot?"],

    },

    #['New York Yankees', 'Green Bay Packers', 'Boston Red Sox', 'Golden State Warriors', 'Chicago Bulls', 'Boston Celtics',
    #'Kansas City Chiefs', 'Los Angeles Lakers', 'Williams Grand Prix Engineering', 'Buffalo Bills', 'Dallas Cowboys',
    #'Washington Redskins', 'Atlanta Falcons', 'Vegas Golden Knights',
    'sports_team': {
        'athlete': ["Who's your favorite player in the {entity}?"],
        'gameplay': ["{entity} have been through so many ups and downs. What are some great moments you remember?"]
    },
    #['Michael Jordan', 'Ifeanyi George', 'LeBron James', 'Thomas Partey', 'Tom Brady', 'George Best',
    #'Simone Biles', 'Lionel Messi', 'Thierry Henry', 'Mike Tyson', 'Patrick Mahomes',
    'athlete': {
        'career': ["What do you think of {entity}'s career performance?"],
        'style': ["What do you like {entity}'s playing style?"]
    },
    #['Mathematics', 'Education', 'Science', 'Artificial intelligence', 'Politics', 'Electronics', 'Animation',
    # 'Art', 'Astronomy', 'Chemistry', 'Physics', 'Psychology',
    'academic_subject': {
        # includes classic subjects like Anthropology but also things like Animation, World Population, Construction
        'concept': ["If you could learn anything about {entity}, what would you want to learn?"],
        #'application': ["What would you like to do after learning {entity}?"],  # this assumes that the user is going to learn about {entity} (i.e. they're in an educational program on it), and I think we'll get a lot of "I'm not learning {entity}" responses. Maybe we just remove this question?
    },
    #['My Neighbor Totoro', 'A Silent Voice (film)', 'Ocean Waves (film)', 'Bleach (TV series)', 'Vampire Knight',
    # 'Tokyo Ghoul', 'Hunter × Hunter', 'Georgie!', 'Spirited Away',
    'anime': {
        'fictional_character': ["What do you think about the characters in {entity}, did you have any favorites?"],
        'plot': ["What was your favorite moment in the anime?", "What did you like about {entity}'s story?"],
    },

    #['Jack Black', 'Gad Elmaleh', 'Kevin Hart', 'Jim Carrey', 'Whoopi Goldberg', 'Gérard Depardieu', 'Donald Glover',
    # 'John Oliver', 'Seth Rogen', 'Justin Timberlake', 'Russell Brand', 'Billy Eichner', 'Robin Williams', 'Charle',
    #'Ben Schwartz'
    'comedian': {
        'style': ["What about {entity}'s act tickles your funny bone?"],  # "what about their style" is hard to answer. easier to answer version: "What parts of {entity}'s act tickles your funny bone?"
    },
    #['Taylor Swift', 'Ariana Grande', 'Michael Jackson', 'Billie Eilish', 'Elvis Presley', 'Beyoncé',
    # 'Katy Perry', 'Will Smith', 'Zac Efron', 'Idina Menzel', 'Justin Bieber',
    'musician': {
        # There might be some actors in here
        'song': ["What would be your favorite song by {entity}?"],
        'style': ["What do you like about {entity}'s performance style?"]
    },
    #['Dwayne Johnson', 'Tom Holland (actor)', 'Jean Benguigui', 'Chris Pratt', 'Keanu Reeves', 'Alfre Woodard', 'Harrison Ford',
    #'Josh Gad', 'Brad Pitt', 'James Earl Jones', 'John Wayne', 'Frank Welker', 'Johnny Depp', 'John Kani',
    'actor': {
        'film': ["Which movie by {entity} do you like the most?"],
        'style': ["What do you like about {entity}'s acting?"],
    },

    # ['Abraham Lincoln', 'Donald Trump', 'George Washington', 'Alexander Hamilton', 'Barack Obama', 'Ronald Reagan',
    # 'Arnold Schwarzenegger', 'Franklin D. Roosevelt', 'Michelle Obama', 'Julius Caesar', 'Cleopatra', 'Winston Churchill',
    # 'Rodrigo Duterte', 'Jimmy Carter',
    'politician': {
        'policies': ["What do you think about the ideas that {entity} stands for?"],
        'personal_life': ["What do you think about {entity}'s legacy?"],
    },

    #'Florida', 'Hawaii', 'Mexico', 'California', 'Italy', 'Paris', 'New York (state)', 'Washington (state)', 'United States',
    # 'Colorado', 'Texas', 'Turkey', 'Canada', 'Las Vegas', 'Philippines', 'India', 'London',
    'location': {
        'poi': ["I'm thinking about visiting {entity} but I'm not sure what to do when I'm there. Do you have any thoughts about what I should do?",
                "When I visit places, I love to take some unique photos. Do you have any ideas for where I could take a cool selfie in {entity}?" ,
                "What do you think is the most interesting thing about visiting {entity}?"]
        # {entity} could be the US so we shouldn't say we've never been at all
    },

    # ['Coffee', 'Banana', 'Avocado', 'Chicken', 'Pizza', 'Pasta', 'Hamburger', 'Spaghetti', 'Taco', 'Cheese',
    # 'Rice', 'Sushi',
    'food': {
        # Might be a dish or an ingredient, a food or drink
        # strawberry, wine, cake, garlic, tic tac, chocolate, nutella, leek, ravioli, hamburger, cinnamon
        # The only way I can see to get all of these to (kinda) work is to precede with "some" or "a bit of"
        'misc': ["What do you like best about {entity}?",
                 "What is it about {entity} that you love?"],
        'taste': ["I find it interesting how people experience taste in different ways. How would you describe the taste of {entity}?",
                  "Recently, I've been trying to appreciate my food more by really noticing how it tastes. How would you describe the taste of {entity}?"],
        'food': ["I love trying out new flavor combinations. What do you like to have {entity} with?",
                 "It's amazing how creative people are when creating new foods and dishes. What do you like to have {entity} with?"],
    },
    'human': {
        # These should be NEUTRAL in opinion, as people can be controversial
        # The person might be alive or dead
        'personal_life': ["What do you think about {entity}'s life?"],
        'legacy': ["What do you think about the legacy that {entity} left behind?"],
    },

    ##### Ignored entity groups

    # Should be ignored
    'group_of_people': [  ],# Be VERY CAREFUL

    # ['TikTok', 'Instagram', 'Twitter', 'Facebook', 'Amazon (company)', 'Spotify', 'Hulu', 'Amazon Prime', 'Pinterest',
    # 'Wikipedia', 'IMDb', 'Snapchat', 'Reddit', 'Wiki', 'Box (company)', 'Discord (software)', 'Peacock (streaming service)',
    # 'Stuff (website)', 'Google Play', 'Signal (software)', 'The New York Times', 'Blog', 'Twitch (service)', 'Rotten Tomatoes',
    # 'Kickstarter', 'Popcorn Time', 'Napster', 'CBS All Access', 'Bing (search engine)', 'Skype', 'Steam (service)']
    'app_or_website': [ ],

    #['Pokémon', 'Kamen Rider', 'Star Trek', 'Naruto', 'Power Rangers', 'The Muppets', "Five Nights at Freddy's",
    #'Indiana Jones (franchise)', 'Ben 10', 'Kingsman (franchise)', 'Fairy Tail', 'Planet of the Apes',
    #'Terminator (franchise)']
    'media_franchise': [],

    #['The Walt Disney Company', 'Xiaomi', 'Nintendo', 'Google', 'Walmart', 'Costco', 'Zoom Video Communications', 'Tesla, Inc.',
    # 'Universal Pictures', 'Apple Inc.', 'Medium (website)', 'Honda', 'Sony',
    'company': [ ],

    # ['Online shopping', 'IPad', 'MacOS', 'Computer', 'Laptop', 'IPhone', 'Podcast', 'Cloud computing', 'World Wide Web',
    # 'Email', 'Website',
    'general_technology': [
        # These are a mix of things that should be pluralized like "laptop" and things that shouldn't like "cloud computing"
        # There are more like "laptop" so these templates work better for that, while still avoiding pluralizing
    ],

    # ['Lego', 'Xbox', 'Nintendo Switch', 'Barbie', 'PlayStation', 'Hot Wheels', 'Slime (toy)', 'Xbox One',
    # 'Nerf', 'PlayStation 4', 'My Little Pony', 'PlayStation 3', 'Wii U', 'Wii']
    'toy': [],
    'family_member': [ ],

    # Mix of breeds and animals, so leaving for now
    # 'Dog', 'Cat', 'Kitten', 'German Shepherd', 'Golden Retriever', 'French Bulldog', 'Beagle', 'Chihuahua (dog)', 'Puppy',
    'pet': [],
    'painting': [],  # Skipping because too specific
    'dance': [],  # ['Ballet', 'Contemporary dance'], very few examples to generalize

    'dancer': [],  # ['Robert (choreographer)', "Charli D'Amelio", 'Cameron Boyce', 'Misty Copeland']

    'artist': [
        # Not necessarily visual art - "artist" is a broad category including actors, musicians etc
        # There's also some weird non-artist people in here who might be controversial (e.g. Elon Musk, Napoleon) so
        # leaving out questions here
    ],

    # ['Switzerland', 'Roman Empire']
    # skipping because don't have enough good examples
    'historical_period': [
    ],

    'clothing': [],  # ['Watch', 'Surgical mask', 'Shoe', 'Crop top', 'Backpack', 'Jeans']
    'fashion_designer': [],  # ['Kim Kardashian', 'Coco Chanel', 'Kylie Jenner', 'Simonetta Stefanelli']

    # Mix of categories and specific vehicles, so ignoring for now
    # ['Bicycle', 'Motorcycle', 'Airplane', 'Car', 'Truck', 'Mini', 'Battleship', 'Kayak', 'Cruise ship', 'USNS Comfort (T-AH-20)',
    # 'AeroVironment RQ-11 Raven', 'Chevrolet Silverado',
    'mode_of_transport': [
    ],
    'animal': {},
    'taxon': [],
}


# Check that all the keys in ACKNOWLEDGMENT_DICTIONARY are in ENTITY_GROUPS_FOR_CLASSIFICATION
for k in OPEN_QUESTIONS_DICTIONARY:
    assert hasattr(ENTITY_GROUPS_FOR_CLASSIFICATION, k), f"ACKNOWLEDGMENT_DICTIONARY contains a key '{k}' not present in ENTITY_GROUPS"

# Check that they all end in ending token
for phrase_dict in OPEN_QUESTIONS_DICTIONARY.values():
    if phrase_dict:
        for return_type, phrases in phrase_dict.items():
            for p in phrases:
                assert any(p.endswith(ending_token) for ending_token in ['.', '!', '?']), f'acknowledgement phrase "{p}" does not end in an ending token'
