from functools import cmp_to_key
from chirpy.core.util import infl
from chirpy.core.entity_linker.entity_groups import EntityGroupsForExpectedType
from chirpy.response_generators.food.yaml_files.supernodes.nlg_word_lists import FOODS, INGREDIENTS, CATEGORIES

import logging
logger = logging.getLogger('chirpylogger')

def get_food_data(food):
    return FOODS[food.lower()]

def get_attribute(food):
    if food is None: return None, None
    food = food.lower()
    if food not in FOODS: return None, None
    food_data = get_food_data(food)
    if 'ingredients' in food_data:
        return 'ingredient', sample_ingredient(food)
    elif 'texture' in food_data:
        return 'texture', food_data['texture']
    return None, None

def get_ingredients_in(food: str) -> set:
    """Returns ingredients in a food"""
    food = food.lower()
    if food not in FOODS: return None
    food_data = get_food_data(food)
    return food_data.get('ingredients', None)

BAD_INGREDIENTS = ['binding agent', 'sweeteners']

def sample_ingredient(food):
    ingredients = get_ingredients_in(food)
    def key(a, b):
        if a in BAD_INGREDIENTS: return 1
        if b in BAD_INGREDIENTS: return -1
        if len(a.split()) > 4: return 1
        if len(b.split()) > 4: return -1
        return INGREDIENTS[a] - INGREDIENTS[b]
    ingredients = sorted(ingredients, key=cmp_to_key(key))
    return ingredients[0]

def is_ingredient(food: str):
    food = food.lower()
    return any('ingredients' in item_data and food in item_data['ingredients'] for item, item_data in FOODS.items())

CUSTOM_QUESTIONS = {
    "hamburger": ("I just love biting into a juicy hamburger, especially with melted cheese on top! What's your favorite topping to put on a hamburger?",
                  "adding a fried egg, it makes it so rich and delicious"),
    "sandwich":  ("It's just so cool to me that you can take anything you want and put it in your sandwich. What's your favorite sandwich filling?",
                  "a simple bacon, lettuce, and tomato sandwich, it's my favorite thing for lunch"),
    "fried rice": ("Fried rice is one of my favorites! I just love all the different things you can put in it. What's your favorite thing to put in fried rice?",
                   "mine with cabbage and teriyaki chicken, it really hits the spot for me"),
    "pizza":      ("I love eating pizza, especially when it's late at night! What's your favorite pizza topping?",
                   "a nice mushroom pizza"),
    "salad":      ("A crunchy salad really hits the spot for me sometimes! I love putting croutons and ranch in my salad. What do you like in your salads?",
                   "nice cheesy croutons and a douse of olive oil"),
    "pasta":      ("I love how versatile pasta is! There are so many different kinds of sauces and toppings to choose from, I could eat pasta every day of the week. What kind of pasta do you like?",
                   "spaghetti carbonara – the bacon and cheese are so savory together"),
    "pastry":     ("Pastries are my favorite way to start the morning. I love how crunchy and buttery they are! What kind of pastry is your favorite?",
                   "apple danish, so simple yet delicious"),
    "doughnut":   ("I love a nice sugary donut! I probably shouldn't be eating them for breakfast, but I do anyway. What's your favorite kind of doughnut?",
                   "just a plain maple glazed donut"),
    "bagel":      ("A nice chewy bagel is my favorite way to start the day, especially with some cream cheese or jelly on top! What's your favorite kind of bagel?",
                   "I really love the everything bagel, it's everything"),
    "roast beef": ("Roast beef is one of my favorite dishes! The way it tastes and smells when it's cooking is amazing! What's your favorite thing to eat roast beef with?",
                   "a side of mashed potatoes"),
    "ice cream": ("Honestly, ice cream is my favorite dessert. It's so yummy, I can't get enough of it whether it's in a cone, cup, or ice cream bar. What's your favorite flavor?",
                  "butterscotch pecan"),
    "coffee": ("I love drinking coffee! A nice cup of coffee is my favorite way to start the day. What's your favorite coffee drink?",
               "mocha. The chocolate and coffee go so well together"),
    "cake": ("I really love cake! I guess you could say I have a bit of a sweet tooth. What's your favorite type of cake?",
             "cheesecake topped with blueberry coulis"),
    "popcorn": ("I love popcorn because it’s so crunchy and has such a cool texture! What’s your favorite popcorn topping?",
                "kettle corn with cheese powder"),
    "ramen": ("I really enjoy eating ramen! It's simple to make and always tastes fantastic. What's your favorite flavor of ramen?",
              "chicken flavored ramen"),
    "cereal": ("I love having cereal! It's one of my favorite breakfast foods. What's your favorite cereal?",
               "muesli with fresh fruit and honey. It has a great crunchy texture!"),
    "bread": ("I love bread! There are so many things you can do with it. What's your favorite type of bread?",
              "bread with anko, which is red bean paste"),
    "potato chip": ("Potato chips are great! They're so delicious and crunchy. What's your favorite potato chip flavor?",
                    "sea salt and pepper"),
    "burrito": ("Burritos are great because you can put all sorts of tasty things in them! What are your favorite toppings?",
                "adding carnitas with large amounts of salsa and cheese")
}

def get_custom_question(cur_food):
    cur_food = cur_food.lower()
    if cur_food in CUSTOM_QUESTIONS:
        return CUSTOM_QUESTIONS[cur_food][0]
    return None

def is_known_food(food: str) -> bool:
    """Make sure to call this first, all of the following functions assume input is in FOODS"""
    logger.primary_info(str((food.lower() in FOODS) or is_ingredient(food) or get_custom_question(food)))
    return (food.lower() in FOODS) or is_ingredient(food) or get_custom_question(food)

def get_best_attribute(food):
    food_data = get_food_data(food)
    if 'ingredients' in food_data:
        return 'has_ingredient'
    elif 'texture' in food_data:
        return 'texture'
    elif is_ingredient(food):
        return 'is_ingredient'
    else:
        return None

def get_time_comment(year, food):
    if 'century' in year: intyear = int(year.replace('st', '').replace('th', '').replace('nd', '').replace('rd', '').replace(' century', '').replace('BC', '').strip()) * 100
    elif year.endswith('s'): intyear = int(year[:-1])
    elif 'era' in year: intyear = 0
    else: intyear = int(year)
    if intyear < 1700:
        if all(x.isdigit() for x in year): year = f"the year {year}"
        if 'century' in year or 'era' in year: year = f"the {year}"
        return f"{year}", f"I can't believe people have been eating {food} for so long!"
    return None # the "modern" comment tends to be quite silly

def get_food_data(food):
    return FOODS[food.lower()]

def get_factoid(cur_entity):
    food = cur_entity.name.lower()
    talkable_food = cur_entity.talkable_name

    copula = infl('was', cur_entity.is_plural)
    have = infl('have', cur_entity.is_plural)

    if food not in FOODS: return None
    food_data = get_food_data(food)
    if 'year' in food_data and 'origin' in food_data and get_time_comment(food_data['year'], talkable_food) is not None:
        year, time_comment = get_time_comment(food_data['year'], talkable_food)
        return f"Did you know that {talkable_food} {copula} first made in {food_data['origin']} around {year}? {time_comment}"
    elif 'year' in food_data and get_time_comment(food_data['year'], talkable_food) is not None:
        year, time_comment = get_time_comment(food_data['year'], talkable_food)
        if time_comment is not None: return f"Did you know that {talkable_food} {have} been made since {year}? {time_comment}"
    elif 'origin' in food_data:
        return f"Did you know that {talkable_food} {copula} originally from {food_data['origin']}?"
    return None

def is_subclassable(food: str):
    return food.lower() in CATEGORIES

def get_best_candidate_user_entity(rg, utterance, cur_food):
    def condition_fn(entity_linker_result, linked_span, entity):
        return EntityGroupsForExpectedType.food_related.matches(entity) and entity.name != cur_food
    entity = rg.state_manager.current_state.entity_linker.top_ent(condition_fn) or rg.state_manager.current_state.entity_linker.top_ent()
    if entity is not None:
        user_answer = entity.talkable_name
        plural = entity.is_plural
    else:
        nouns = rg.state_manager.current_state.corenlp['nouns']
        if len(nouns):
            user_answer = nouns[-1]
            plural = True
        else:
            user_answer = utterance.replace('i like', '').replace('my favorite', '').replace('i love', '')
            plural = True

    return user_answer, plural